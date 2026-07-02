import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ApiError } from "@/types/auth";
import type { Project } from "@/types/project";

const projectSchema = z.object({
  project_name: z.string().min(1, "Project name is required").max(255),
  description: z.string().max(500).optional(),
  language: z.string().min(1, "Language is required").max(100),
  framework: z.string().max(100).optional(),
  version: z.string().max(50).optional(),
});

type ProjectForm = z.infer<typeof projectSchema>;

interface CreateProjectDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: ProjectForm) => Promise<void>;
  editProject?: Project | null;
}

const languageOptions = [
  "Python",
  "JavaScript",
  "TypeScript",
  "Java",
  "Go",
  "Rust",
  "C++",
  "C#",
  "Ruby",
  "PHP",
  "Swift",
  "Kotlin",
  "Other",
];

export function CreateProjectDialog({
  open,
  onClose,
  onSubmit,
  editProject,
}: CreateProjectDialogProps) {
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProjectForm>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      project_name: "",
      description: "",
      language: "",
      framework: "",
      version: "",
    },
  });

  useEffect(() => {
    if (open) {
      if (editProject) {
        reset({
          project_name: editProject.project_name,
          description: editProject.description ?? "",
          language: editProject.language,
          framework: editProject.framework ?? "",
          version: editProject.version ?? "",
        });
      } else {
        reset({
          project_name: "",
          description: "",
          language: "",
          framework: "",
          version: "",
        });
      }
      setError(null);
    }
  }, [open, editProject, reset]);

  const handleFormSubmit = async (data: ProjectForm) => {
    setError(null);
    try {
      await onSubmit(data);
      onClose();
    } catch (err) {
      if (axios.isAxiosError<ApiError>(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("An unexpected error occurred");
      }
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <div
            className="fixed inset-0 z-50 bg-black/50"
            onClick={onClose}
          />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="w-full max-w-lg rounded-xl border border-border bg-popover shadow-modal"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b border-border px-6 py-4">
                <h2 className="text-lg font-semibold text-foreground">
                  {editProject ? "Edit Project" : "Create Project"}
                </h2>
                <button
                  onClick={onClose}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form
                onSubmit={handleSubmit(handleFormSubmit)}
                className="space-y-5 p-6"
              >
                {error && (
                  <div className="rounded-md bg-red-50 p-3 text-sm text-destructive">
                    {error}
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="project_name">Project name *</Label>
                  <Input
                    id="project_name"
                    placeholder="My Project"
                    {...register("project_name")}
                  />
                  {errors.project_name && (
                    <p className="text-sm text-destructive">
                      {errors.project_name.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <textarea
                    id="description"
                    rows={3}
                    className="flex w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-ring resize-none"
                    placeholder="Brief description of your project"
                    {...register("description")}
                  />
                  {errors.description && (
                    <p className="text-sm text-destructive">
                      {errors.description.message}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="language">Language *</Label>
                    <select
                      id="language"
                      className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-ring"
                      {...register("language")}
                    >
                      <option value="">Select language</option>
                      {languageOptions.map((lang) => (
                        <option key={lang} value={lang}>
                          {lang}
                        </option>
                      ))}
                    </select>
                    {errors.language && (
                      <p className="text-sm text-destructive">
                        {errors.language.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="framework">Framework</Label>
                    <Input
                      id="framework"
                      placeholder="React, Django, etc."
                      {...register("framework")}
                    />
                    {errors.framework && (
                      <p className="text-sm text-destructive">
                        {errors.framework.message}
                      </p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="version">Version</Label>
                  <Input
                    id="version"
                    placeholder="1.0.0"
                    {...register("version")}
                  />
                  {errors.version && (
                    <p className="text-sm text-destructive">
                      {errors.version.message}
                    </p>
                  )}
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={onClose}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting
                      ? editProject
                        ? "Saving..."
                        : "Creating..."
                      : editProject
                        ? "Save changes"
                        : "Create project"}
                  </Button>
                </div>
              </form>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
