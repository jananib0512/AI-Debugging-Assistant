import { zodResolver } from "@hookform/resolvers/zod";
import axios, { type AxiosProgressEvent } from "axios";
import { motion } from "framer-motion";
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  File,
  FileArchive,
  FileWarning,
  FolderOpen,
  HardDrive,
  Loader2,
  RefreshCw,
  Upload,
  X,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { extractProject } from "@/lib/projects";
import { cn } from "@/lib/utils";
import type { ApiError } from "@/types/auth";
import type { Project } from "@/types/project";

const MAX_SIZE = 1024 * 1024 * 1024;
const SUPPORTED_FORMATS = [".zip", ".tar.gz", ".tgz", ".7z", ".rar"] as const;
const ACCEPT_STRING = ".zip,.tar.gz,.tgz,.7z,.rar";

const projectSchema = z.object({
  project_name: z.string().min(1, "Project name is required"),
  language: z.string().min(1, "Language is required"),
});

type ProjectForm = z.infer<typeof projectSchema>;

const languageOptions = [
  "Python", "JavaScript", "TypeScript", "Java", "Go",
  "Rust", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin", "Other",
];

interface UploadState {
  file: File | null;
  status: "idle" | "selected" | "uploading" | "uploaded";
  progress: number;
  uploadedBytes: number;
  totalBytes: number;
  elapsedMs: number;
  error: string | null;
  project: Project | null;
}

interface ExtractionState {
  status: "idle" | "extracting" | "extracted" | "failed";
  error: string | null;
}

export function UploadPage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [upload, setUpload] = useState<UploadState>({
    file: null,
    status: "idle",
    progress: 0,
    uploadedBytes: 0,
    totalBytes: 0,
    elapsedMs: 0,
    error: null,
    project: null,
  });
  const [extraction, setExtraction] = useState<ExtractionState>({
    status: "idle",
    error: null,
  });
  const [dragOver, setDragOver] = useState(false);
  const [extractionStatusMessage, setExtractionStatusMessage] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset: resetForm,
  } = useForm<ProjectForm>({
    resolver: zodResolver(projectSchema),
    defaultValues: { project_name: "", language: "" },
  });

  const validateFile = (file: File): string | null => {
    const name = file.name.toLowerCase();
    const valid = SUPPORTED_FORMATS.some((fmt) => name.endsWith(fmt));
    if (!valid) {
      return "Unsupported archive format. Supported formats: .zip, .tar.gz, .tgz, .7z, .rar";
    }
    if (file.size === 0) {
      return "File is empty";
    }
    if (file.size > MAX_SIZE) {
      return "File exceeds the maximum upload size of 1 GB";
    }
    return null;
  };

  const handleFile = useCallback((file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setUpload({
        file: null,
        status: "idle",
        progress: 0,
        uploadedBytes: 0,
        totalBytes: 0,
        elapsedMs: 0,
        error: validationError,
        project: null,
      });
      return;
    }
    setUpload({
      file,
      status: "selected",
      progress: 0,
      uploadedBytes: 0,
      totalBytes: file.size,
      elapsedMs: 0,
      error: null,
      project: null,
    });
    setExtraction({ status: "idle", error: null });
    resetForm();
  }, [resetForm]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleBrowse = () => inputRef.current?.click();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  };

  const handleCancel = () => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setUpload({
      file: null,
      status: "idle",
      progress: 0,
      uploadedBytes: 0,
      totalBytes: 0,
      elapsedMs: 0,
      error: null,
      project: null,
    });
    setExtraction({ status: "idle", error: null });
  };

  const handleReset = () => {
    setUpload({
      file: null,
      status: "idle",
      progress: 0,
      uploadedBytes: 0,
      totalBytes: 0,
      elapsedMs: 0,
      error: null,
      project: null,
    });
    setExtraction({ status: "idle", error: null });
    resetForm();
  };

  const startExtraction = async (project: Project) => {
    setExtraction({ status: "extracting", error: null });
    try {
      const extracted = await extractProject(project.id);
      setExtraction({ status: "extracted", error: null });
      setUpload((prev) => ({ ...prev, project: extracted }));
    } catch (err) {
      let message = "Extraction failed. Please try again.";
      if (axios.isAxiosError<ApiError>(err) && err.response?.data?.detail) {
        message = err.response.data.detail;
      }
      setExtraction({ status: "failed", error: message });
    }
  };

  useEffect(() => {
    if (extraction.status !== "extracting") {
      setExtractionStatusMessage("");
      return;
    }
    const messages = [
      "Scanning project archive...",
      "Ignoring dependency and build folders...",
      "Counting source files...",
      "Extracting workspace...",
      "Validating project structure...",
      "Cleaning up temporary files...",
    ];
    let index = 0;
    setExtractionStatusMessage(messages[index]!);
    const interval = setInterval(() => {
      index = (index + 1) % messages.length;
      setExtractionStatusMessage(messages[index]!);
    }, 2500);
    return () => clearInterval(interval);
  }, [extraction.status]);

  const handleRetryExtraction = () => {
    if (upload.project) {
      startExtraction(upload.project);
    }
  };

  const onSubmit = async (data: ProjectForm) => {
    if (!upload.file) return;

    setUpload((prev) => ({
      ...prev, status: "uploading", progress: 0, uploadedBytes: 0,
      totalBytes: upload.file!.size, elapsedMs: 0, error: null,
    }));
    setExtraction({ status: "idle", error: null });

    const controller = new AbortController();
    abortRef.current = controller;
    const uploadStartTime = Date.now();

    try {
      const createRes = await api.post<Project>("/projects", {
        project_name: data.project_name,
        language: data.language,
      });

      const project = createRes.data;

      const formData = new FormData();
      formData.append("file", upload.file);

      const uploadRes = await api.post<Project>(
        `/projects/${project.id}/upload`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          signal: controller.signal,
          onUploadProgress: (e: AxiosProgressEvent) => {
            const elapsed = Date.now() - uploadStartTime;
            setUpload((prev) => ({
              ...prev,
              progress: e.total ? Math.round((e.loaded * 100) / e.total) : 0,
              uploadedBytes: e.loaded,
              totalBytes: e.total || prev.totalBytes,
              elapsedMs: elapsed,
            }));
          },
        },
      );

      setUpload({
        file: null,
        status: "uploaded",
        progress: 100,
        uploadedBytes: upload.file!.size,
        totalBytes: upload.file!.size,
        elapsedMs: Date.now() - uploadStartTime,
        error: null,
        project: uploadRes.data,
      });

      startExtraction(uploadRes.data);
    } catch (err) {
      if (axios.isCancel(err)) {
        setUpload({
          file: null,
          status: "idle",
          progress: 0,
          uploadedBytes: 0,
          totalBytes: 0,
          elapsedMs: 0,
          error: null,
          project: null,
        });
        return;
      }

      let message = "Upload failed. Please try again.";
      if (axios.isAxiosError<ApiError>(err) && err.response?.data?.detail) {
        message = err.response.data.detail;
      }

      setUpload((prev) => ({
        ...prev,
        status: "selected",
        progress: 0,
        error: message,
      }));
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const project = upload.project;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-[#111827]">Upload Project</h2>
        <p className="text-sm text-[#6B7280]">
          Upload your project for debugging and analysis
        </p>
      </div>

      {extraction.status === "extracted" && project ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <div className="flex flex-col items-center justify-center py-16 px-6">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-green-50 mb-4">
                <CheckCircle2 className="h-7 w-7 text-[#10B981]" />
              </div>
              <h3 className="text-lg font-medium text-[#111827]">
                Extraction Completed
              </h3>
              <p className="mt-1 text-sm text-[#6B7280] text-center max-w-sm">
                {project.project_name} has been uploaded and extracted successfully.
                The workspace is ready.
              </p>

              <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
                {project.total_files !== null && (
                  <div className="flex items-center gap-2 rounded-lg bg-[#F3F4F6] px-4 py-2.5">
                    <File className="h-4 w-4 text-[#6B7280]" />
                    <div>
                      <p className="text-xs text-[#6B7280]">Files</p>
                      <p className="text-sm font-semibold text-[#111827]">
                        {project.total_files.toLocaleString()}
                      </p>
                    </div>
                  </div>
                )}
                {project.total_folders !== null && (
                  <div className="flex items-center gap-2 rounded-lg bg-[#F3F4F6] px-4 py-2.5">
                    <FolderOpen className="h-4 w-4 text-[#6B7280]" />
                    <div>
                      <p className="text-xs text-[#6B7280]">Folders</p>
                      <p className="text-sm font-semibold text-[#111827]">
                        {project.total_folders.toLocaleString()}
                      </p>
                    </div>
                  </div>
                )}
                {project.extraction_time_ms !== null && (
                  <div className="flex items-center gap-2 rounded-lg bg-[#F3F4F6] px-4 py-2.5">
                    <Loader2 className="h-4 w-4 text-[#6B7280]" />
                    <div>
                      <p className="text-xs text-[#6B7280]">Time</p>
                      <p className="text-sm font-semibold text-[#111827]">
                        {formatTime(project.extraction_time_ms)}
                      </p>
                    </div>
                  </div>
                )}
                {project.workspace_path && (
                  <div className="flex items-center gap-2 rounded-lg bg-[#F3F4F6] px-4 py-2.5">
                    <HardDrive className="h-4 w-4 text-[#6B7280]" />
                    <div>
                      <p className="text-xs text-[#6B7280]">Workspace</p>
                      <p className="text-sm font-semibold text-[#111827]">
                        storage/workspaces/{project.id}/
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
                <Button
                  variant="default"
                  className="gap-2"
                  onClick={() => navigate(`/workspace/${project.id}`)}
                >
                  <ArrowRight className="h-4 w-4" />
                  Open Workspace
                </Button>
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={handleReset}
                >
                  <Upload className="h-4 w-4" />
                  Upload another project
                </Button>
              </div>
            </div>
          </Card>
        </motion.div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card>
                <div className="p-6">
                  <h3 className="text-sm font-semibold text-[#111827] mb-4">
                    Upload project archive
                  </h3>

                  <input
                    ref={inputRef}
                    type="file"
                    accept={ACCEPT_STRING}
                    className="hidden"
                    onChange={handleInputChange}
                  />

                  {upload.status === "uploaded" && extraction.status === "extracting" ? (
                    <div className="space-y-6 py-8">
                      <div className="flex flex-col items-center justify-center">
                        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-blue-50 mb-4">
                          <Loader2 className="h-7 w-7 text-[#2563EB] animate-spin" />
                        </div>
                        <h3 className="text-lg font-medium text-[#111827]">
                          {extractionStatusMessage || "Extracting..."}
                        </h3>
                        <p className="mt-1 text-sm text-[#6B7280] text-center max-w-sm">
                          Please wait while we prepare your workspace.
                        </p>
                        {upload.uploadedBytes > 0 && (
                          <p className="mt-2 text-xs text-[#6B7280]">
                            Uploaded {formatSize(upload.uploadedBytes)} in {formatTime(upload.elapsedMs)}
                          </p>
                        )}
                      </div>
                      <div className="mx-auto w-full max-w-sm">
                        <div className="h-2 w-full rounded-full bg-[#F3F4F6] overflow-hidden">
                          <motion.div
                            initial={{ width: "0%" }}
                            animate={{ width: "80%" }}
                            transition={{
                              duration: 1.5,
                              repeat: Infinity,
                              repeatType: "reverse",
                              ease: "easeInOut",
                            }}
                            className="h-full rounded-full bg-[#2563EB]"
                          />
                        </div>
                      </div>
                    </div>
                  ) : upload.status === "uploaded" && extraction.status === "failed" ? (
                    <div className="space-y-4 py-6">
                      <div className="flex flex-col items-center justify-center">
                        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-50 mb-4">
                          <XCircle className="h-7 w-7 text-[#EF4444]" />
                        </div>
                        <h3 className="text-lg font-medium text-[#111827]">
                          Extraction Failed
                        </h3>
                        <p className="mt-1 text-sm text-[#6B7280] text-center max-w-sm">
                          {extraction.error}
                        </p>
                      </div>
                      <div className="flex justify-center gap-3 pt-2">
                        <Button
                          className="gap-2"
                          onClick={handleRetryExtraction}
                        >
                          <RefreshCw className="h-4 w-4" />
                          Retry Extraction
                        </Button>
                        <Button
                          variant="outline"
                          onClick={handleReset}
                        >
                          Start Over
                        </Button>
                      </div>
                    </div>
                  ) : (upload.status === "selected" || upload.status === "uploading") ? (
                    <div className="space-y-4">
                      <div className="flex items-center gap-4 rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-4">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 shrink-0">
                          <FileArchive className="h-5 w-5 text-[#2563EB]" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-[#111827] truncate">
                            {upload.file?.name}
                          </p>
                          <p className="text-xs text-[#6B7280]">
                            {upload.file && formatSize(upload.file.size)}
                          </p>
                        </div>
                        <button
                          onClick={handleReset}
                          className="text-[#6B7280] hover:text-[#111827] transition-colors shrink-0"
                          disabled={upload.status === "uploading"}
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>

                      {upload.status === "uploading" && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-[#6B7280]">Uploading...</span>
                            <span className="font-medium text-[#111827]">
                              {upload.progress}%
                            </span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-[#F3F4F6] overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${upload.progress}%` }}
                              transition={{ duration: 0.3 }}
                              className="h-full rounded-full bg-[#2563EB]"
                            />
                          </div>
                          <div className="flex items-center justify-between text-xs text-[#6B7280]">
                            <span>
                              {formatSize(upload.uploadedBytes)} / {formatSize(upload.totalBytes)}
                            </span>
                            {upload.elapsedMs > 0 && upload.uploadedBytes > 0 && (
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {formatTime(upload.elapsedMs)}
                                {upload.progress > 0 && upload.progress < 100 && (
                                  <span>
                                    · ~{formatTime(
                                      Math.round(
                                        (upload.elapsedMs / upload.progress) * (100 - upload.progress),
                                      ),
                                    )} left
                                  </span>
                                )}
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 pt-2">
                        <div className="grid gap-4 sm:grid-cols-2">
                          <div className="space-y-1.5">
                            <Label htmlFor="project_name">Project name</Label>
                            <Input
                              id="project_name"
                              placeholder="My Project"
                              disabled={upload.status === "uploading"}
                              {...register("project_name")}
                            />
                            {errors.project_name && (
                              <p className="text-xs text-[#EF4444]">
                                {errors.project_name.message}
                              </p>
                            )}
                          </div>
                          <div className="space-y-1.5">
                            <Label htmlFor="language">Language</Label>
                            <select
                              id="language"
                              disabled={upload.status === "uploading"}
                              className="flex h-10 w-full rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-sm text-[#111827] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB] focus-visible:border-[#2563EB] disabled:opacity-50"
                              {...register("language")}
                            >
                              <option value="">Select language</option>
                              {languageOptions.map((lang) => (
                                <option key={lang} value={lang}>{lang}</option>
                              ))}
                            </select>
                            {errors.language && (
                              <p className="text-xs text-[#EF4444]">
                                {errors.language.message}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="flex gap-3 pt-1">
                          {upload.status === "uploading" ? (
                            <Button
                              type="button"
                              variant="outline"
                              className="gap-2"
                              onClick={handleCancel}
                            >
                              <X className="h-4 w-4" />
                              Cancel
                            </Button>
                          ) : (
                            <>
                              <Button type="submit" className="gap-2">
                                <Upload className="h-4 w-4" />
                                Upload & Extract
                              </Button>
                              <Button
                                type="button"
                                variant="ghost"
                                onClick={handleReset}
                              >
                                Choose different file
                              </Button>
                            </>
                          )}
                        </div>
                      </form>
                    </div>
                  ) : (
                    <div
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onClick={handleBrowse}
                      className={cn(
                        "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors",
                        dragOver
                          ? "border-[#2563EB] bg-[#EFF6FF]"
                          : "border-[#E5E7EB] hover:border-[#2563EB]/50 hover:bg-[#F9FAFB]",
                      )}
                    >
                      <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[#F3F4F6] mb-4">
                        <Upload className="h-6 w-6 text-[#6B7280]" />
                      </div>
                      <h3 className="text-sm font-medium text-[#111827]">
                        Drag & drop your archive file here
                      </h3>
                      <p className="mt-1 text-xs text-[#6B7280]">
                        or click to browse
                      </p>
                      <div className="mt-4 flex items-center gap-3 text-[11px] text-[#6B7280]">
                        <span className="flex items-center gap-1">
                          <FileArchive className="h-3.5 w-3.5" />
                          .zip, .tar.gz, .tgz, .7z, .rar
                        </span>
                        <span className="h-3 w-px bg-[#E5E7EB]" />
                        <span>Max 1 GB</span>
                      </div>
                    </div>
                  )}

                  {upload.error && (
                    <motion.div
                      initial={{ opacity: 0, y: -4 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-4 flex items-start gap-3 rounded-lg bg-red-50 p-4"
                    >
                      <XCircle className="h-5 w-5 text-[#EF4444] shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-[#EF4444]">
                          {upload.error}
                        </p>
                      </div>
                      <button
                        onClick={() => setUpload((prev) => ({ ...prev, error: null }))}
                        className="text-sm font-medium text-[#EF4444] hover:text-[#DC2626] shrink-0"
                      >
                        Dismiss
                      </button>
                    </motion.div>
                  )}
                </div>
              </Card>
            </motion.div>
          </div>

          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <Card>
                <div className="p-6 space-y-4">
                  <h3 className="text-sm font-semibold text-[#111827]">
                    Upload requirements
                  </h3>
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <FileArchive className="h-4 w-4 text-[#2563EB] mt-0.5 shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-[#111827]">
                          Multiple archive formats
                        </p>
                        <p className="text-xs text-[#6B7280] mt-0.5">
                          Supports .zip, .tar.gz, .tgz, .7z, and .rar archives.
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <HardDrive className="h-4 w-4 text-[#2563EB] mt-0.5 shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-[#111827]">
                          Maximum 1 GB
                        </p>
                        <p className="text-xs text-[#6B7280] mt-0.5">
                          Upload size is limited to 1 GB per project.
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <FileWarning className="h-4 w-4 text-[#2563EB] mt-0.5 shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-[#111827]">
                          Validation & security
                        </p>
                        <p className="text-xs text-[#6B7280] mt-0.5">
                          Corrupted, password-protected, or oversized archives (over 100k files, over 2 GB) are rejected.
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <FolderOpen className="h-4 w-4 text-[#2563EB] mt-0.5 shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-[#111827]">
                          Auto-extraction
                        </p>
                        <p className="text-xs text-[#6B7280] mt-0.5">
                          Archives are automatically extracted to a dedicated workspace while preserving folder structure.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          </div>
        </div>
      )}
    </div>
  );
}
