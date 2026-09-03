/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState } from "react";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
import { HelpOutline, PagesOutline } from "@makeplane/propel/icons";
import { useTranslation } from "@plane/i18n";
// ui
import { CustomMenu } from "@plane/ui";
// components
import { AppSidebarItem } from "@/components/sidebar/sidebar-item";
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
  // states
  const [isNeedHelpOpen, setIsNeedHelpOpen] = useState(false);

  return (
    <CustomMenu
      customButton={
        <AppSidebarItem
          variant="button"
          item={{
            icon: <HelpOutline className="size-5" />,
            isActive: isNeedHelpOpen,
          }}
        />
      }
      menuButtonOnClick={() => !isNeedHelpOpen && setIsNeedHelpOpen(true)}
      onMenuClose={() => setIsNeedHelpOpen(false)}
      placement="bottom-end"
      maxHeight="lg"
      closeOnSelect
    >
      {GUIAS.map((guia) => (
        <CustomMenu.MenuItem
          key={guia.slug}
          onClick={() => router.push(getGuiaLink(workspaceSlug?.toString() ?? "", guia.slug))}
        >
          <div className="flex items-center gap-x-2 rounded-sm text-11">
            <PagesOutline className="h-3.5 w-3.5 text-secondary" height={14} width={14} />
            <span className="text-11">{guia.label}</span>
          </div>
        </CustomMenu.MenuItem>
      ))}
      <div className="my-1 border-t border-subtle" />
      <CustomMenu.MenuItem>
        <button
          type="button"
          onClick={() => toggleShortcutsListModal(true)}
          className="justify-sbg-layer-211 flex w-full items-center hover:bg-layer-1"
        >
          <span className="text-11">{t("keyboard_shortcuts")}</span>
        </button>
      </CustomMenu.MenuItem>
      <div className="mt-1 border-t border-subtle px-1 pt-2 text-11 text-secondary">
        <PlaneVersionNumber />
      </div>
    </CustomMenu>
  );
});
