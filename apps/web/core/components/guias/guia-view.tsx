/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import Markdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
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
 * `.ProseMirror` is styled for an editor: `white-space: pre-wrap`, so the newlines
 * react-markdown leaves between blocks would render as blank lines, and a text
 * caret over content nobody can type into. Both live in an unlayered stylesheet,
 * which outranks any Tailwind utility — hence the inline style.
 */
const READ_ONLY_STYLE = { whiteSpace: "normal", cursor: "auto" } as const;

/**
 * The document editor tags every node it renders, and the stylesheet in
 * @plane/editor keys off those classes: `editor-heading-block` and
 * `editor-paragraph-block` carry the font sizes and the vertical rhythm, while
 * `.editor-container.document-editor .ProseMirror > *` is what constrains the
 * content to `--editor-content-width` and centers it. Markdown gives us plain
 * tags, so we put the same classes back on the way out — without them the page
 * renders unstyled and edge to edge.
 */
const MARKDOWN_COMPONENTS: Components = {
  h1: ({ node: _node, children, ...props }) => (
    <h1 className="editor-heading-block" {...props}>
      {children}
    </h1>
  ),
  h2: ({ node: _node, children, ...props }) => (
    <h2 className="editor-heading-block" {...props}>
      {children}
    </h2>
  ),
  h3: ({ node: _node, children, ...props }) => (
    <h3 className="editor-heading-block" {...props}>
      {children}
    </h3>
  ),
  h4: ({ node: _node, children, ...props }) => (
    <h4 className="editor-heading-block" {...props}>
      {children}
    </h4>
  ),
  h5: ({ node: _node, children, ...props }) => (
    <h5 className="editor-heading-block" {...props}>
      {children}
    </h5>
  ),
  h6: ({ node: _node, children, ...props }) => (
    <h6 className="editor-heading-block" {...props}>
      {children}
    </h6>
  ),
  p: ({ node: _node, ...props }) => <p className="editor-paragraph-block" {...props} />,
  ul: ({ node: _node, ...props }) => <ul className="list-disc space-y-(--list-spacing-y) pl-7" {...props} />,
  ol: ({ node: _node, ...props }) => <ol className="list-decimal space-y-(--list-spacing-y) pl-7" {...props} />,
  li: ({ node: _node, ...props }) => <li className="not-prose space-y-2" {...props} />,
  // the markdown files are ours, but every link in them still leaves the app.
  // the classes are the ones the editor's link extension applies.
  a: ({ node: _node, children, ...props }) => (
    <a
      className="cursor-pointer text-accent-secondary underline underline-offset-[3px] transition-colors hover:text-accent-primary"
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
    </a>
  ),
  // code blocks have no editor node view here, so they get their frame from us
  pre: ({ node: _node, ...props }) => (
    <pre className="my-2 overflow-x-auto rounded-md border border-subtle bg-layer-1 p-3" {...props} />
  ),
};

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
              {/* the title takes its width and font size from `.page-title-editor .ProseMirror` */}
              <div className="ProseMirror" style={READ_ONLY_STYLE}>
                <h1 className="break-words">{guia.label}</h1>
              </div>
            </div>
          </div>
          <div className={cn(containerClassName, "document-editor h-full p-0 pb-64")}>
            <div
              className="ProseMirror prose-brand prose-headings:font-display font-default max-w-full prose"
              style={READ_ONLY_STYLE}
            >
              <Markdown components={MARKDOWN_COMPONENTS} remarkPlugins={[remarkGfm]}>
                {guia.content}
              </Markdown>
            </div>
          </div>
        </div>
      </div>
    </Row>
  );
});
