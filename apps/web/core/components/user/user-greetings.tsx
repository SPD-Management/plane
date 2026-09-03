/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// plane types
import { useTranslation } from "@plane/i18n";
// hooks
import type { IUser } from "@plane/types";
import { useCurrentTime } from "@/hooks/use-current-time";
// types

export interface IUserGreetingsView {
  user: IUser;
}

export function UserGreetingsView(props: IUserGreetingsView) {
  const { user } = props;
  // current time hook
  const { currentTime } = useCurrentTime();
  // store hooks
  const { t, currentLocale } = useTranslation();

  // Always read the hour with a fixed locale + h23 cycle: this value is parsed as a
  // number to pick the greeting, so it must not follow the display locale.
  const hour = new Intl.DateTimeFormat("en-US", {
    timeZone: user?.user_timezone,
    hourCycle: "h23",
    hour: "numeric",
  }).format(currentTime);

  const date = new Intl.DateTimeFormat(currentLocale, {
    timeZone: user?.user_timezone,
    month: "short",
    day: "numeric",
  }).format(currentTime);

  const weekDay = new Intl.DateTimeFormat(currentLocale, {
    timeZone: user?.user_timezone,
    weekday: "long",
  }).format(currentTime);

  const timeString = new Intl.DateTimeFormat(currentLocale, {
    timeZone: user?.user_timezone,
    hourCycle: "h23", // Use 24-hour format
    hour: "2-digit",
    minute: "2-digit",
  }).format(currentTime);

  const greeting = parseInt(hour, 10) < 12 ? "morning" : parseInt(hour, 10) < 18 ? "afternoon" : "evening";
  // The greeting is a single key per period of the day: languages with gender or
  // honorific agreement (pt-BR "Bom dia" / "Boa noite", ja "{name}さん、こんばんは")
  // cannot be assembled from a "good" fragment plus a period fragment.
  const greetingName = [user?.first_name, user?.last_name].filter(Boolean).join(" ").trim() || user?.display_name;

  return (
    <div className="my-6 flex flex-col items-center">
      <h2 className="text-center text-20 font-semibold">{t(`good_${greeting}`, { name: greetingName })}</h2>
      <h5 className="flex items-center gap-2 font-medium text-placeholder">
        <div>{greeting === "morning" ? "🌤️" : greeting === "afternoon" ? "🌥️" : "🌙️"}</div>
        <div>
          {weekDay}, {date} {timeString}
        </div>
      </h5>
    </div>
  );
}
