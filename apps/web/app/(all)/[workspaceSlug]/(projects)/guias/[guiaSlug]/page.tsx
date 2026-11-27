/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import Link from "next/link";
// plane imports
import { Button as ButtonElement } from "@makeplane/propel/elements/button";
// components
import { PageHead } from "@/components/core/page-title";
import { GuiaView } from "@/components/guias/guia-view";
import { getGuiaBySlug } from "@/components/guias/registry";
// local imports
import type { Route } from "./+types/page";

export default function GuiaPage({ params }: Route.ComponentProps) {
  const { workspaceSlug, guiaSlug } = params;
  // derived values
  const guia = getGuiaBySlug(guiaSlug);

  if (!guia)
    return (
      <div className="flex h-full w-full flex-col items-center justify-center">
        <h3 className="text-center text-16 font-semibold">Página não encontrada</h3>
        <p className="mt-3 text-center text-13 text-secondary">A página que você está tentando acessar não existe.</p>
        <div className="mt-5">
          <ButtonElement variant="secondary" size="md" stretch="auto" render={<Link href={`/${workspaceSlug}`} />}>
            Voltar para o início
          </ButtonElement>
        </div>
      </div>
    );

  return (
    <>
      <PageHead title={guia.label} />
      <div className="flex h-full flex-col justify-between">
        <div className="relative flex h-full w-full flex-shrink-0 flex-col overflow-hidden">
          <GuiaView guia={guia} />
        </div>
      </div>
    </>
  );
}
