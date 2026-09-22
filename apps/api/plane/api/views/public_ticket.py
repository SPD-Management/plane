# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import os
import uuid
import html
import base64
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from plane.db.models import Project, Issue, State, FileAsset
from plane.db.models.issue import IssueAttachment
from plane.settings.storage import S3Storage


class PublicTicketEndpoint(APIView):
    """
    Public endpoint for receiving support tickets from external forms without auth.
    Saves attached evidence files as real FileAsset and IssueAttachment objects so images 
    appear both inside the Tiptap editor description and in the Plane attachments section.
    """
    permission_classes = [AllowAny]

    def options(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_200_OK)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        return response

    def post(self, request):
        data = request.data
        solicitante = str(data.get("solicitante", "") or "").strip()
        email = str(data.get("email", "") or "").strip()
        lista_filtro = str(data.get("lista_filtro", "") or "").strip()
        problema = str(data.get("problema", "") or "").strip()
        descricao = str(data.get("descricao", "") or "").strip()
        evidencias = data.get("evidencias", [])  # list of {name, type, data}
        
        target_project_id = data.get(
            "project_id", 
            os.environ.get("PUBLIC_TICKET_PROJECT_ID", "c3615582-e0c3-450e-a46a-79abbc2a680d")
        )

        if not problema:
            return Response(
                {"error": "O campo 'Problema' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Fetch target project or fallback gracefully
        project = None
        if target_project_id:
            try:
                project = Project.objects.filter(id=target_project_id).first()
            except Exception:
                project = None
        
        if not project:
            project = Project.objects.first()

        if not project:
            return Response(
                {"error": "Nenhum projeto encontrado no Plane para vincular o ticket."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2. Fetch default state
        state = State.objects.filter(project=project, group__in=["backlog", "unstarted"]).first()
        if not state:
            state = State.objects.filter(project=project).first()

        # 3. Create initial Issue object
        issue_name = problema if problema else "Ticket do Formulário Público"
        issue = Issue.objects.create(
            project=project,
            workspace=project.workspace,
            name=issue_name,
            description_html="<p>Processando solicitação...</p>",
            description_stripped=f"Solicitante: {solicitante}\nEmail: {email}\nURL Lista/Filtro: {lista_filtro}\nProblema: {problema}\nDescricao: {descricao}",
            priority="medium",
            state=state,
            external_source="public_form",
        )

        # 4. Save evidence files as real FileAsset and IssueAttachment objects
        evidence_html = ""
        attachment_links = []

        if evidencias and isinstance(evidencias, list):
            storage = S3Storage()
            for idx, item in enumerate(evidencias):
                if isinstance(item, dict) and item.get("data"):
                    file_name = str(item.get("name", f"evidencia-{idx+1}.jpg")).strip()
                    file_data = str(item.get("data"))
                    file_type = str(item.get("type", "image/jpeg")).strip()

                    try:
                        # Decode base64 data URL
                        if "," in file_data:
                            header, b64str = file_data.split(",", 1)
                        else:
                            b64str = file_data

                        decoded_bytes = base64.b64decode(b64str)
                        size_bytes = len(decoded_bytes)
                        content_file = ContentFile(decoded_bytes, name=file_name)

                        # Generate clean S3 key
                        asset_key = f"{project.workspace.id}/{uuid.uuid4().hex}-{file_name}"

                        # Upload file to S3/MinIO storage
                        upload_success = storage.upload_file(
                            content_file,
                            object_name=asset_key,
                            content_type=file_type,
                        )
                        if not upload_success:
                            print(f"Aviso: upload_file retornou False para {file_name}")

                        # Create FileAsset (Main Plane asset model used by frontend editor & attachments panel)
                        file_asset = FileAsset.objects.create(
                            attributes={
                                "name": file_name,
                                "type": file_type,
                                "size": size_bytes,
                            },
                            asset=asset_key,
                            size=size_bytes,
                            workspace=project.workspace,
                            project=project,
                            issue=issue,
                            entity_type=FileAsset.EntityTypeContext.ISSUE_ATTACHMENT,
                            entity_identifier=str(issue.id),
                            is_uploaded=True,
                            external_source="public_form",
                        )

                        # Also create legacy IssueAttachment object as fallback
                        try:
                            IssueAttachment.objects.create(
                                issue=issue,
                                project=project,
                                workspace=project.workspace,
                                asset=asset_key,
                                attributes={
                                    "name": file_name,
                                    "type": file_type,
                                    "size": size_bytes,
                                },
                                external_source="public_form",
                            )
                        except Exception as e:
                            print(f"Aviso ao criar IssueAttachment secundário: {e}")

                        # Build image URLs
                        asset_api_url = file_asset.asset_url or f"/api/assets/v2/workspaces/{project.workspace.slug}/projects/{project.id}/issues/{issue.id}/attachments/{file_asset.id}/"
                        asset_full_url = request.build_absolute_uri(asset_api_url)

                        s3_direct_url = storage.generate_presigned_url(asset_key, expiration=86400, filename=file_name)
                        if s3_direct_url:
                            s3_direct_url = s3_direct_url.replace("http://plane-minio:9000", "http://localhost:9000")
                        else:
                            s3_direct_url = asset_full_url

                        attachment_links.append({
                            "id": str(file_asset.id),
                            "name": file_name,
                            "api_url": asset_api_url,
                            "full_url": asset_full_url,
                            "s3_url": s3_direct_url,
                            "type": file_type,
                        })
                    except Exception as err:
                        print(f"Erro ao salvar anexo {file_name}: {err}")

        # 5. Build rich HTML description without any <div> tags (pure Tiptap compatible tags)
        solicitante_clean = html.escape(solicitante or "Não informado")
        email_clean = html.escape(email or "Não informado")
        
        if lista_filtro.startswith("http://") or lista_filtro.startswith("https://"):
            lista_clean_html = f'<a href="{html.escape(lista_filtro)}" target="_blank" rel="noopener noreferrer">{html.escape(lista_filtro)}</a>'
        else:
            lista_clean_html = html.escape(lista_filtro or "Não informado")
            
        descricao_clean = html.escape(descricao or "").replace("\n", "<br/>")

        if attachment_links:
            evidence_html += '<hr/><h3>Evidências Anexadas</h3>'
            for att in attachment_links:
                fname = html.escape(att["name"])
                furl = html.escape(att["s3_url"] or att["full_url"])
                ftype = att["type"]

                evidence_html += f'<p><strong>📎 {fname}</strong></p>'
                if ftype.startswith("image/"):
                    evidence_html += f'<p><image-component src="{furl}"></image-component></p>'
                    evidence_html += f'<p><img src="{furl}" alt="{fname}"/></p>'
                elif ftype.startswith("video/"):
                    evidence_html += f'<p><video controls><source src="{furl}" type="{ftype}"></video></p>'
                
                if furl:
                    evidence_html += f'<p><a href="{furl}" target="_blank" download="{fname}">📥 Baixar {fname}</a></p>'

        description_html = f"""<p><strong>Solicitante:</strong> {solicitante_clean}</p><p><strong>E-mail do Usuário:</strong> <a href="mailto:{email_clean}">{email_clean}</a></p><p><strong>URL da Lista / Filtro:</strong> {lista_clean_html}</p><hr/><h3>Descrição do Problema</h3><p>{descricao_clean}</p>{evidence_html}""".strip()

        # 6. Save updated description_html
        issue.description_html = description_html
        issue.save()

        return Response(
            {
                "success": True,
                "message": "Ticket e evidências criados com sucesso!",
                "issue": {
                    "id": str(issue.id),
                    "sequence_id": issue.sequence_id,
                    "identifier": f"{project.identifier}-{issue.sequence_id}",
                    "name": issue.name,
                    "project_id": str(project.id),
                    "project_name": project.name,
                    "attachments_count": len(attachment_links),
                },
            },
            status=status.HTTP_201_CREATED,
        )
