import { motion } from "framer-motion";
import {
  BarChart3,
  FileSearch,
  FolderKanban,
  Layers,
  Loader2,
  Search,
  X,
  HardDrive,
  Clock,
  FolderOpen,
  Upload,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { FileTree } from "@/components/workspace/file-tree";
import { MetadataPanel } from "@/components/workspace/metadata-panel";
import { getFileMetadata, getWorkspaceTree, listWorkspaces } from "@/lib/workspace";
import { getProject } from "@/lib/projects";
import type { FileMetadata, TreeEntry, WorkspaceListItem } from "@/types/workspace";
import type { Project } from "@/types/project";

export function WorkspacePage() {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId?: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [tree, setTree] = useState<TreeEntry | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<FileMetadata | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [treeLoaded, setTreeLoaded] = useState(false);
  const treeRef = useRef<HTMLDivElement>(null);

  const loadTree = useCallback(async (pid: number) => {
    setLoading(true);
    setError(null);
    try {
      const [proj, treeData] = await Promise.all([
        getProject(pid),
        getWorkspaceTree(pid),
      ]);
      setProject(proj);
      setTree(treeData);
      setTreeLoaded(true);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to load workspace";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (projectId) {
      loadTree(Number(projectId));
    } else {
      setProject(null);
      setTree(null);
      setSelectedPath(null);
      setMetadata(null);
      setTreeLoaded(false);
    }
  }, [projectId, loadTree]);

  const handleSelect = useCallback(
    async (path: string, type: "file" | "directory") => {
      setSelectedPath(path);
      setMetadata(null);
      if (type === "file" && project) {
        try {
          const meta = await getFileMetadata(project.id, path);
          setMetadata(meta);
        } catch {
          // metadata fetch failed silently
        }
      }
    },
    [project],
  );

  const filteredTree = useMemo(() => {
    if (!tree || !searchQuery) return tree;
    return filterTreeForSearch(tree, searchQuery);
  }, [tree, searchQuery]);

  if (!projectId) {
    return <WorkspaceListView navigate={navigate} />;
  }

  if (loading && !treeLoaded) {
    return (
      <div className="space-y-8">
        <div>
          <h2 className="text-lg font-semibold text-[#111827]">Workspace</h2>
          <p className="text-sm text-[#6B7280]">Loading workspace...</p>
        </div>
        <Card>
          <div className="flex flex-col items-center justify-center py-24">
            <Loader2 className="h-8 w-8 text-[#2563EB] animate-spin mb-4" />
            <p className="text-sm text-[#6B7280]">Loading project files...</p>
          </div>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div>
          <h2 className="text-lg font-semibold text-[#111827]">Workspace</h2>
          <p className="text-sm text-[#6B7280]">Error loading workspace</p>
        </div>
        <Card>
          <div className="flex flex-col items-center justify-center py-24">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-50 mb-4">
              <Layers className="h-7 w-7 text-[#EF4444]" />
            </div>
            <h3 className="text-lg font-medium text-[#111827]">
              Failed to load workspace
            </h3>
            <p className="mt-1 text-sm text-[#6B7280] text-center max-w-sm">
              {error}
            </p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[#111827]">
            {project?.project_name || "Workspace"}
          </h2>
          <p className="text-sm text-[#6B7280]">
            {project?.language} &middot; Project #{projectId}
          </p>
        </div>
        <button
          onClick={() => navigate(`/projects/${projectId}/overview`)}
          className="flex items-center gap-2 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-sm font-medium text-[#374151] hover:bg-[#F9FAFB] hover:text-[#111827] transition-colors"
        >
          <BarChart3 className="h-4 w-4" />
          Overview
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="lg:col-span-3">
          <Card className="overflow-hidden">
            <div className="flex items-center gap-2 border-b border-[#E5E7EB] px-3 py-2">
              <Search className="h-4 w-4 text-[#9CA3AF] shrink-0" />
              <Input
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-7 border-none bg-transparent px-0 text-sm shadow-none focus-visible:ring-0 placeholder:text-[#9CA3AF]"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="flex h-5 w-5 items-center justify-center rounded text-[#9CA3AF] hover:text-[#6B7280] hover:bg-[#F3F4F6] transition-colors"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            <div
              ref={treeRef}
              className="overflow-y-auto"
              style={{ maxHeight: "calc(100vh - 320px)" }}
            >
              {filteredTree ? (
                <FileTree
                  tree={filteredTree}
                  selectedPath={selectedPath}
                  onSelect={handleSelect}
                  searchQuery={searchQuery}
                />
              ) : (
                <div className="flex flex-col items-center justify-center py-16">
                  <FileSearch className="h-8 w-8 text-[#9CA3AF] mb-2" />
                  <p className="text-sm text-[#6B7280]">
                    {searchQuery
                      ? "No matching files"
                      : "No files found in workspace"}
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="lg:col-span-1">
          {metadata ? (
            <motion.div
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
            >
              <MetadataPanel metadata={metadata} />
            </motion.div>
          ) : selectedPath ? (
            <Card>
              <div className="flex flex-col items-center justify-center py-12 px-4">
                <FolderKanban className="h-6 w-6 text-[#9CA3AF] mb-2" />
                <p className="text-sm text-[#6B7280] text-center">
                  Select a file to view its properties
                </p>
              </div>
            </Card>
          ) : (
            <Card>
              <div className="flex flex-col items-center justify-center py-12 px-4">
                <Layers className="h-6 w-6 text-[#9CA3AF] mb-2" />
                <p className="text-sm text-[#6B7280] text-center">
                  Select a file to view its properties
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function formatDate(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function WorkspaceListView({ navigate }: { navigate: ReturnType<typeof useNavigate> }) {
  const [workspaces, setWorkspaces] = useState<WorkspaceListItem[]>([]);
  const [loadingWorkspaces, setLoadingWorkspaces] = useState(true);

  useEffect(() => {
    listWorkspaces()
      .then((res) => setWorkspaces(res.workspaces))
      .catch(() => setWorkspaces([]))
      .finally(() => setLoadingWorkspaces(false));
  }, []);

  if (loadingWorkspaces) {
    return (
      <div className="space-y-8">
        <div>
          <h2 className="text-lg font-semibold text-[#111827]">Workspace</h2>
          <p className="text-sm text-[#6B7280]">Loading workspaces...</p>
        </div>
        <Card>
          <div className="flex flex-col items-center justify-center py-24">
            <Loader2 className="h-8 w-8 text-[#2563EB] animate-spin mb-4" />
          </div>
        </Card>
      </div>
    );
  }

  if (workspaces.length === 0) {
    return (
      <div className="space-y-8">
        <div>
          <h2 className="text-lg font-semibold text-[#111827]">Workspace</h2>
          <p className="text-sm text-[#6B7280]">Browse your extracted project files</p>
        </div>
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <div className="flex flex-col items-center justify-center py-24">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#F3F4F6] mb-6">
                <Layers className="h-7 w-7 text-[#6B7280]" />
              </div>
              <h3 className="text-lg font-medium text-[#111827]">No active workspace</h3>
              <p className="mt-1 text-sm text-[#6B7280] text-center max-w-sm">
                Upload and extract a project to get started.
              </p>
              <button
                onClick={() => navigate("/upload")}
                className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-4 py-2 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors"
              >
                <Upload className="h-4 w-4" />
                Upload Project
              </button>
            </div>
          </Card>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-[#111827]">Workspace</h2>
        <p className="text-sm text-[#6B7280]">{workspaces.length} active workspace{workspaces.length > 1 ? "s" : ""}</p>
      </div>
      <div className="grid gap-4">
        {workspaces.map((ws, i) => (
          <motion.div
            key={ws.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.06 }}
          >
            <Card className="overflow-hidden">
              <div className="p-5">
                <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#DBEAFE]">
                    <HardDrive className="h-6 w-6 text-[#2563EB]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-semibold text-[#111827] truncate">{ws.project_name}</h3>
                    <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[#6B7280]">
                      <span>{ws.language}</span>
                      <span className="flex items-center gap-1">
                        <FolderOpen className="h-3 w-3" />
                        {ws.total_files ?? "—"} files
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(ws.extracted_at)}
                      </span>
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                        ws.status === "active"
                          ? "bg-[#D1FAE5] text-[#065F46]"
                          : "bg-[#FEF3C7] text-[#92400E]"
                      }`}>
                        {ws.status === "active" ? "Active" : "Inactive"}
                      </span>
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    <button
                      onClick={() => navigate(`/workspace/${ws.project_id}`)}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-[#2563EB] px-3.5 py-2 text-sm font-medium text-white hover:bg-[#1D4ED8] transition-colors"
                    >
                      <FolderKanban className="h-4 w-4" />
                      Browse Files
                    </button>
                    <button
                      onClick={() => navigate(`/projects/${ws.project_id}/overview`)}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3.5 py-2 text-sm font-medium text-[#374151] hover:bg-[#F9FAFB] transition-colors"
                    >
                      <BarChart3 className="h-4 w-4" />
                      Overview
                    </button>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function filterTreeForSearch(tree: TreeEntry, query: string): TreeEntry | null {
  if (!query) return tree;
  const q = query.toLowerCase();
  const nameMatch = tree.name.toLowerCase().includes(q);

  let filteredChildren: TreeEntry[] | null = null;
  if (tree.children) {
    filteredChildren = tree.children
      .map((child) => filterTreeForSearch(child, query))
      .filter((child): child is TreeEntry => child !== null);
  }

  if (!nameMatch && (!filteredChildren || filteredChildren.length === 0)) {
    return null;
  }

  return {
    ...tree,
    children: filteredChildren || null,
  };
}
