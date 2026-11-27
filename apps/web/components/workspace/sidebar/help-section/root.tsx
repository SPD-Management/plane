/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// SPD: o menu de ajuda lista os guias internos (components/guias/registry.ts)
// no lugar de documentação/contato de vendas/fórum/novidades do upstream.
import React from "react";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
import { HelpOutline, PagesOutline } from "@makeplane/propel/icons";
import { useTranslation } from "@plane/i18n";
// ui
import { Icon } from "@makeplane/propel/components/icon";
import { Menu, MenuContent, MenuFooter, MenuItem, MenuSeparator, MenuTrigger } from "@makeplane/propel/components/menu";
import { Tooltip } from "@makeplane/propel/components/tooltip";
import { IconButton } from "@makeplane/propel/elements/icon-button";
// components
import { PlaneVersionNumber } from "@/components/global/version-number";
import { GUIAS, getGuiaLink } from "@/components/guias/registry";
// hooks
import { usePowerK } from "@/hooks/store/use-power-k";
import { useAppRouter } from "@/hooks/use-app-router";

export const HelpMenuRoot = observer(function HelpMenuRoot() {
  // router
  const router = useAppRouter();
  const { workspaceSlug } = useParams();
  // store hooks
  const { t } = useTranslation();
  const { toggleShortcutsListModal } = usePowerK();

  return (
    <Menu>
      <Tooltip label={t("power_k.group_titles.help")} side="bottom">
        <MenuTrigger
          render={
            <IconButton
              variant="ghost"
              size="md"
              aria-label={t("power_k.group_titles.help")}
              render={<button type="button" className="data-popup-open:bg-layer-transparent-active" />}
            >
              <HelpOutline className="size-4.5" />
            </IconButton>
          }
        />
      </Tooltip>
      <MenuContent
        side="bottom"
        align="end"
        footer={
          <MenuFooter>
            <PlaneVersionNumber />
          </MenuFooter>
        }
      >
        {GUIAS.map((guia) => (
          <MenuItem
            key={guia.slug}
            icon={<Icon icon={PagesOutline} tint="secondary" />}
            label={guia.label}
            onClick={() => router.push(getGuiaLink(workspaceSlug?.toString() ?? "", guia.slug))}
          />
        ))}
        <MenuSeparator />
        <MenuItem label={t("keyboard_shortcuts")} onClick={() => toggleShortcutsListModal(true)} />
      </MenuContent>
    </Menu>
  );
});
