/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useForm } from "react-hook-form";
import { ThoughtsOutline } from "@makeplane/propel/icons";
import { Button } from "@makeplane/propel/components/button";
import type { IFormattedInstanceConfiguration, TInstanceAIConfigurationKeys } from "@plane/types";
// components
import type { TControllerInputFormField } from "@/components/common/controller-input";
import { ControllerInput } from "@/components/common/controller-input";
import { TOAST_TYPE, setToast } from "@/providers/toast";
// hooks
import { useInstance } from "@/hooks/store";

type IInstanceAIForm = {
  config: IFormattedInstanceConfiguration;
};

type AIFormValues = Record<TInstanceAIConfigurationKeys, string>;

export function InstanceAIForm(props: IInstanceAIForm) {
  const { config } = props;
  // store
  const { updateInstanceConfigurations } = useInstance();
  // form data
  const {
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<AIFormValues>({
    defaultValues: {
      LLM_PROVIDER: config["LLM_PROVIDER"] || "openai",
      LLM_API_KEY: config["LLM_API_KEY"],
      LLM_MODEL: config["LLM_MODEL"],
      LLM_BASE_URL: config["LLM_BASE_URL"],
    },
  });

  const aiFormFields: TControllerInputFormField<AIFormValues>[] = [
    {
      key: "LLM_PROVIDER",
      type: "text",
      label: "Provider",
      description: (
        <>
          One of <code>openai</code>, <code>anthropic</code>, <code>gemini</code>, <code>zai</code>,{" "}
          <code>zai-coding</code> or <code>openai-compatible</code>.
        </>
      ),
      placeholder: "openai",
      error: Boolean(errors.LLM_PROVIDER),
      required: false,
    },
    {
      key: "LLM_MODEL",
      type: "text",
      label: "LLM Model",
      description: <>The model name as the provider spells it, e.g. gpt-4o-mini or glm-5.3-flash.</>,
      placeholder: "gpt-4o-mini",
      error: Boolean(errors.LLM_MODEL),
      required: false,
    },
    {
      key: "LLM_API_KEY",
      type: "password",
      label: "API key",
      description: <>The API key issued by the provider above.</>,
      placeholder: "sk-asddassdfasdefqsdfasd23das3dasdcasd",
      error: Boolean(errors.LLM_API_KEY),
      required: false,
    },
    {
      key: "LLM_BASE_URL",
      type: "text",
      label: "Base URL",
      description: <>Leave empty to use the provider default. Required for openai-compatible endpoints.</>,
      placeholder: "https://api.openai.com/v1",
      error: Boolean(errors.LLM_BASE_URL),
      required: false,
    },
  ];

  const onSubmit = async (formData: AIFormValues) => {
    const payload: Partial<AIFormValues> = { ...formData };

    await updateInstanceConfigurations(payload)
      .then(() =>
        setToast({
          type: TOAST_TYPE.SUCCESS,
          title: "Success",
          message: "AI Settings updated successfully",
        })
      )
      .catch((err) => console.error(err));
  };

  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <div>
          <div className="pb-1 text-18 font-medium text-primary">LLM provider</div>
          <div className="text-13 font-regular text-tertiary">
            Any OpenAI-compatible provider works here - OpenAI, Z.AI (GLM), or your own gateway.
          </div>
        </div>
        <div className="grid-col grid w-full grid-cols-1 items-center justify-between gap-x-12 gap-y-8 lg:grid-cols-3">
          {aiFormFields.map((field) => (
            <ControllerInput
              key={field.key}
              control={control}
              type={field.type}
              name={field.key}
              label={field.label}
              description={field.description}
              placeholder={field.placeholder}
              error={field.error}
              required={field.required}
            />
          ))}
        </div>
      </div>

      <div className="flex flex-col items-start gap-4">
        <Button
          variant="primary"
          size="md"
          stretch="auto"
          onClick={handleSubmit(onSubmit)}
          loading={isSubmitting}
          label={isSubmitting ? "Saving" : "Save changes"}
        />

        <div className="relative inline-flex items-center gap-1.5 rounded-sm border border-accent-subtle bg-accent-subtle px-4 py-2 text-caption-sm-regular text-accent-secondary">
          <ThoughtsOutline className="size-4" />
          <div>
            If you have a preferred AI models vendor, please get in{" "}
            <a className="font-medium underline" href="https://plane.so/contact">
              touch with us.
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
