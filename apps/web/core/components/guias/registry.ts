/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// content — plain HTML files, edit them to change what each page shows
import comoIntegrarAIaContent from "../../content/guias/como-integrar-a-ia.html?raw";
import ferramentasContent from "../../content/guias/ferramentas.html?raw";
import guiaDeUsoContent from "../../content/guias/guia-de-uso.html?raw";
import nossasFerramentasContent from "../../content/guias/nossas-ferramentas.html?raw";
import novidadesNoAtlasContent from "../../content/guias/novidades-no-atlas.html?raw";
import sobreASpeedioContent from "../../content/guias/sobre-a-speedio.html?raw";

export type TGuia = {
  /** URL segment, rendered at /:workspaceSlug/guias/:guiaSlug */
  slug: string;
  /** Title shown on the page, in the breadcrumb and in the help menu */
  label: string;
  /** Page body, as HTML */
  content: string;
};

/**
 * Static, in-repo pages linked from the help menu. They render with the same
 * typography and layout as a Page, but their content lives in the HTML files
 * imported above instead of in the database.
 *
 * The order here is the order of the entries in the help menu.
 */
export const GUIAS: TGuia[] = [
  {
    slug: "guia-de-uso",
    label: "Guia de uso",
    content: guiaDeUsoContent,
  },
  {
    slug: "novidades-no-atlas",
    label: "Novidades no Atlas",
    content: novidadesNoAtlasContent,
  },
  {
    slug: "sobre-a-speedio",
    label: "Sobre a Speedio",
    content: sobreASpeedioContent,
  },
  {
    slug: "ferramentas",
    label: "Ferramentas",
    content: ferramentasContent,
  },
  {
    slug: "nossas-ferramentas",
    label: "Nossas ferramentas",
    content: nossasFerramentasContent,
  },
  {
    slug: "como-integrar-a-ia",
    label: "Como integrar a IA",
    content: comoIntegrarAIaContent,
  },
];

export const getGuiaBySlug = (slug: string | undefined): TGuia | undefined => GUIAS.find((guia) => guia.slug === slug);

export const getGuiaLink = (workspaceSlug: string, slug: string): string => `/${workspaceSlug}/guias/${slug}`;
