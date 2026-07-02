import { AnimatePresence, motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { useCallback, useState } from "react";

import { FileIcon } from "@/components/workspace/file-icon";
import { cn } from "@/lib/utils";
import type { TreeEntry } from "@/types/workspace";

interface FileTreeProps {
  tree: TreeEntry;
  selectedPath: string | null;
  onSelect: (path: string, type: "file" | "directory") => void;
  searchQuery: string;
  className?: string;
}

interface TreeNodeProps {
  entry: TreeEntry;
  depth: number;
  selectedPath: string | null;
  onSelect: (path: string, type: "file" | "directory") => void;
  searchQuery: string;
  isParentExpanded: boolean;
}

function filterTree(entry: TreeEntry, query: string): TreeEntry | null {
  if (!query) return entry;
  const q = query.toLowerCase();
  const nameMatch = entry.name.toLowerCase().includes(q);

  let filteredChildren: TreeEntry[] | null = null;
  if (entry.children) {
    filteredChildren = entry.children
      .map((child) => filterTree(child, query))
      .filter((child): child is TreeEntry => child !== null);
  }

  if (!nameMatch && (!filteredChildren || filteredChildren.length === 0)) {
    return null;
  }

  return {
    ...entry,
    children: filteredChildren,
  };
}

function TreeNode({
  entry,
  depth,
  selectedPath,
  onSelect,
  searchQuery,
  isParentExpanded,
}: TreeNodeProps) {
  const [expanded, setExpanded] = useState(
    searchQuery.length > 0 && entry.type === "directory",
  );
  const isDir = entry.type === "directory";

  const handleClick = useCallback(() => {
    if (isDir) {
      setExpanded((prev) => !prev);
    }
    onSelect(entry.path, entry.type);
  }, [isDir, entry.path, entry.type, onSelect]);

  const isSelected = selectedPath === entry.path;

  if (!isParentExpanded && !searchQuery) return null;

  const visibleChildren = searchQuery
    ? (entry.children ?? [])
        .map((child) => filterTree(child, searchQuery))
        .filter((child): child is TreeEntry => child !== null)
    : (entry.children ?? []);

  return (
    <div>
      <button
        onClick={handleClick}
        className={cn(
          "flex w-full items-center gap-1 px-2 py-[3px] text-[13px] transition-colors rounded hover:bg-[#F3F4F6]",
          isSelected ? "bg-[#EFF6FF] text-[#2563EB]" : "text-[#374151]",
        )}
        style={{ paddingLeft: `${12 + depth * 16}px` }}
      >
        {isDir ? (
          <ChevronRight
            className={cn(
              "h-3.5 w-3.5 shrink-0 transition-transform text-[#9CA3AF]",
              expanded && "rotate-90",
            )}
          />
        ) : (
          <span className="w-3.5 shrink-0" />
        )}
        <FileIcon
          name={entry.name}
          type={entry.type}
          expanded={expanded}
        />
        <span className="truncate">{entry.name}</span>
      </button>

      <AnimatePresence initial={false}>
        {isDir && expanded && visibleChildren.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15, ease: "easeInOut" }}
          >
            {visibleChildren.map((child) => (
              <TreeNode
                key={child.path}
                entry={child}
                depth={depth + 1}
                selectedPath={selectedPath}
                onSelect={onSelect}
                searchQuery={searchQuery}
                isParentExpanded={true}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function FileTree({
  tree,
  selectedPath,
  onSelect,
  searchQuery,
  className,
}: FileTreeProps) {
  const visibleTree = searchQuery ? filterTree(tree, searchQuery) : tree;

  if (!visibleTree || !visibleTree.children || visibleTree.children.length === 0) {
    return (
      <div className={cn("flex flex-col items-center justify-center py-12 px-4", className)}>
        <FileIcon name="folder" type="directory" className="h-8 w-8 text-[#9CA3AF] mb-2" />
        <p className="text-sm text-[#6B7280]">
          {searchQuery ? "No matching files" : "Empty workspace"}
        </p>
      </div>
    );
  }

  return (
    <div className={cn("py-1", className)}>
      {visibleTree.children.map((child) => (
        <TreeNode
          key={child.path}
          entry={child}
          depth={0}
          selectedPath={selectedPath}
          onSelect={onSelect}
          searchQuery={searchQuery}
          isParentExpanded={true}
        />
      ))}
    </div>
  );
}
