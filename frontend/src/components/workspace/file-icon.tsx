import type { ElementType } from "react";
import {
  Braces,
  Code2,
  Container,
  File,
  FileCode,
  FileJson,
  FileText,
  FileType,
  Globe,
  Hash,
  Hexagon,
  Terminal,
} from "lucide-react";

import { cn } from "@/lib/utils";

const iconMap: Record<string, ElementType> = {
  ".py": Code2,
  ".js": FileCode,
  ".jsx": FileCode,
  ".ts": FileCode,
  ".tsx": FileCode,
  ".html": Globe,
  ".htm": Globe,
  ".css": Braces,
  ".scss": Braces,
  ".sass": Braces,
  ".less": Braces,
  ".json": FileJson,
  ".yaml": FileJson,
  ".md": FileText,
  ".mdx": FileText,
  ".sql": Hash,
  ".java": Braces,
  ".go": Terminal,
  ".rs": Hexagon,
  ".c": FileCode,
  ".cpp": FileCode,
  ".h": FileCode,
  ".hpp": FileCode,
  ".php": FileCode,
  ".rb": Hash,
  ".xml": FileType,
  ".sh": Terminal,
  ".bash": Terminal,
  ".zsh": Terminal,
  ".dockerfile": Container,
};

interface FileIconProps {
  name: string;
  type: "file" | "directory";
  className?: string;
  expanded?: boolean;
}

export function FileIcon({ name, type, className, expanded }: FileIconProps) {
  if (type === "directory") {
    return (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={cn("h-4 w-4 shrink-0", className)}
      >
        {expanded ? (
          <>
            <path d="M5 19a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h4l3 3h7a2 2 0 0 1 2 2v1" />
            <path d="M5 19h14a2 2 0 0 0 2-2v-5a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2Z" />
          </>
        ) : (
          <>
            <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
          </>
        )}
      </svg>
    );
  }

  const ext = name.includes(".")
    ? `.${name.split(".").pop()?.toLowerCase()}`
    : "";

  const IconComponent = ext ? iconMap[ext] : null;

  if (IconComponent) {
    const colorMap: Record<string, string> = {
      ".py": "text-[#3572A5]",
      ".js": "text-[#F7DF1E]",
      ".jsx": "text-[#61DAFB]",
      ".ts": "text-[#3178C6]",
      ".tsx": "text-[#3178C6]",
      ".html": "text-[#E34F26]",
      ".css": "text-[#1572B6]",
      ".scss": "text-[#CC6699]",
      ".json": "text-[#6B7280]",
      ".yaml": "text-[#6B7280]",
      ".md": "text-[#6B7280]",
      ".sql": "text-[#E38C00]",
      ".java": "text-[#ED8B00]",
      ".go": "text-[#00ADD8]",
      ".rs": "text-[#DEA584]",
      ".c": "text-[#555555]",
      ".cpp": "text-[#00599C]",
      ".php": "text-[#777BB4]",
      ".rb": "text-[#CC342D]",
      ".sh": "text-[#4EAA25]",
      ".bash": "text-[#4EAA25]",
    };

    return (
      <IconComponent
        className={cn(
          "h-4 w-4 shrink-0",
          colorMap[ext] || "text-[#6B7280]",
          className,
        )}
      />
    );
  }

  return <File className={cn("h-4 w-4 shrink-0 text-[#6B7280]", className)} />;
}
