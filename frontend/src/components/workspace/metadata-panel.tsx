import { Calendar, File, HardDrive, Hash, Clock } from "lucide-react";

import { Card } from "@/components/ui/card";
import { FileIcon } from "@/components/workspace/file-icon";
import type { FileMetadata } from "@/types/workspace";

interface MetadataPanelProps {
  metadata: FileMetadata;
}

function formatDate(dateString: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(dateString));
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export function MetadataPanel({ metadata }: MetadataPanelProps) {
  return (
    <Card>
      <div className="p-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] mb-4">
          Properties
        </h3>

        <div className="flex items-center gap-3 pb-4 mb-4 border-b border-[#E5E7EB]">
          <FileIcon
            name={metadata.name}
            type={metadata.is_directory ? "directory" : "file"}
            expanded={true}
            className="h-6 w-6"
          />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-[#111827] truncate">
              {metadata.name}
            </p>
            <p className="text-xs text-[#6B7280]">
              {metadata.is_directory ? "Folder" : metadata.extension || "File"}
            </p>
          </div>
        </div>

        <div className="space-y-3">
          {!metadata.is_directory && (
            <div className="flex items-center gap-3">
              <HardDrive className="h-4 w-4 text-[#9CA3AF] shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-xs text-[#6B7280]">Size</p>
                <p className="text-sm text-[#111827]">
                  {formatSize(metadata.size)}
                </p>
              </div>
            </div>
          )}

          <div className="flex items-center gap-3">
            <Hash className="h-4 w-4 text-[#9CA3AF] shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-xs text-[#6B7280]">Extension</p>
              <p className="text-sm text-[#111827]">
                {metadata.is_directory ? "-" : metadata.extension || "(none)"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Calendar className="h-4 w-4 text-[#9CA3AF] shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-xs text-[#6B7280]">Created</p>
              <p className="text-sm text-[#111827]">
                {formatDate(metadata.created_at)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Clock className="h-4 w-4 text-[#9CA3AF] shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-xs text-[#6B7280]">Modified</p>
              <p className="text-sm text-[#111827]">
                {formatDate(metadata.modified_at)}
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <File className="h-4 w-4 text-[#9CA3AF] shrink-0 mt-0.5" />
            <div className="min-w-0 flex-1">
              <p className="text-xs text-[#6B7280]">Path</p>
              <p className="text-sm text-[#111827] break-all">
                {metadata.relative_path}
              </p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
