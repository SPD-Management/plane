/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
// plane imports
import { ERowVariant, Row } from "@plane/ui";
import { cn } from "@plane/utils";
// hooks
import { usePageFilters } from "@/hooks/use-page-filters";
// local imports
import type { TGuia } from "./registry";

type Props = {
  guia: TGuia;
};

/**
 * Renders a static guide with the exact DOM structure a Page uses
 * (#page-content-container > .frame-renderer > .editor-container > .ProseMirror),
 * so it inherits the editor's typography, widths and spacing.
 *
 * The HTML comes from a file in the repo, never from user input, which is why
 * it is injected directly.
 */
export const GuiaView = observer(function GuiaView(props: Props) {
  const { guia } = props;
  // page filters — same font/width preferences the user set on Pages
  const { fontSize, fontStyle, isFullWidth } = usePageFilters();

  const containerClassName = cn("editor-container line-spacing-regular", fontSize, fontStyle);

  return (
    <Row
      className="vertical-scrollbar relative scrollbar-md flex size-full flex-col overflow-x-hidden overflow-y-auto duration-200"
      variant={ERowVariant.HUGGING}
    >
      <div id="page-content-container" className="relative w-full flex-shrink-0">
        <div
          className={cn("frame-renderer w-full flex-grow", {
            "wide-layout": isFullWidth,
          })}
        >
          <div className="relative w-full py-3">
            <div className={cn(containerClassName, "page-title-editor border-none bg-transparent py-3")}>
              <h1 className="text-[2rem] leading-[2.375rem] font-bold tracking-[-2%] break-words">{guia.label}</h1>
            </div>
          </div>
          <div className={cn(containerClassName, "h-full p-0 pb-64")}>
            {/* oxlint-disable-next-line react/no-danger */}
            <div
              // the hand-written HTML has no editor node classes, so code blocks get their
              // padding, background and horizontal scroll from here
              className="ProseMirror [&_pre]:overflow-x-auto [&_pre]:rounded-md [&_pre]:border [&_pre]:border-subtle [&_pre]:bg-layer-1 [&_pre]:p-3"
              // .ProseMirror sets `white-space: pre-wrap`, which is right for editor-generated
              // markup but would preserve the indentation of the hand-written HTML files.
              style={{ whiteSpace: "normal" }}
              dangerouslySetInnerHTML={{ __html: guia.content }}
            />
          </div>
        </div>
      </div>
    </Row>
  );
});
