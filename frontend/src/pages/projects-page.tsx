import { motion } from "framer-motion";
import {
  ArrowUpDown,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Code2,
  FolderKanban,
  Globe,
  Pencil,
  Plus,
  Search,
  Tag,
  Trash2,
} from "lucide-react";
import { useEffect, useState } from "react";

import { CreateProjectDialog } from "@/components/projects/create-project-dialog";
import { DeleteProjectDialog } from "@/components/projects/delete-project-dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  createProject,
  deleteProject,
  listProjects,
  updateProject,
} from "@/lib/projects";
import type {
  Project,
  ProjectCreateInput,
  ProjectUpdateInput,
} from "@/types/project";

function formatDate(dateString: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(dateString));
}

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(12);
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const data = await listProjects({
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
        search: search || undefined,
      });
      setProjects(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [page, sortBy, sortOrder, search]);

  const handleSearch = () => {
    setPage(1);
    setSearch(searchInput);
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const toggleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
    setPage(1);
  };

  const handleCreate = async (data: ProjectCreateInput) => {
    await createProject(data);
    setPage(1);
    await fetchProjects();
  };

  const handleUpdate = async (data: ProjectUpdateInput) => {
    if (!editingProject) return;
    await updateProject(editingProject.id, data);
    setEditingProject(null);
    await fetchProjects();
  };

  const handleDelete = async () => {
    if (!deletingProject) return;
    await deleteProject(deletingProject.id);
    setDeletingProject(null);
    setPage(1);
    await fetchProjects();
  };

  const SortIcon = ({ field }: { field: string }) => {
    if (sortBy !== field) return <ArrowUpDown className="h-3 w-3 text-muted-foreground opacity-50" />;
    return (
      <ArrowUpDown
        className={`h-3 w-3 transition-transform ${
          sortOrder === "asc" ? "rotate-180" : ""
        }`}
      />
    );
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Projects</h2>
          <p className="text-sm text-muted-foreground">
            Manage your debugging projects
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} className="gap-2 shrink-0">
          <Plus className="h-4 w-4" />
          New Project
        </Button>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search projects..."
            className="pl-9"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={handleSearchKeyDown}
          />
        </div>
        {!loading && projects.length > 0 && (
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Sort:</span>
              <button
                onClick={() => toggleSort("project_name")}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Name <SortIcon field="project_name" />
              </button>
              <button
                onClick={() => toggleSort("created_at")}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Date <SortIcon field="created_at" />
              </button>
              <button
                onClick={() => toggleSort("language")}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                Language <SortIcon field="language" />
              </button>
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="rounded-xl border border-border bg-card shadow-card h-48 animate-pulse"
            />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="rounded-xl border border-border bg-card shadow-card flex flex-col items-center justify-center py-24"
        >
          {search ? (
            <>
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary mb-6">
                <Search className="h-7 w-7 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium text-foreground">No results found</h3>
              <p className="mt-1 text-sm text-muted-foreground text-center max-w-sm">
                No projects match your search criteria. Try a different query.
              </p>
              <Button
                variant="ghost"
                className="mt-4"
                onClick={() => {
                  setSearchInput("");
                  setSearch("");
                }}
              >
                Clear search
              </Button>
            </>
          ) : (
            <>
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary mb-6">
                <FolderKanban className="h-7 w-7 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium text-foreground">No projects yet</h3>
              <p className="mt-1 text-sm text-muted-foreground text-center max-w-sm">
                Create your first project to start debugging and analyzing your
                code.
              </p>
              <Button
                onClick={() => setCreateOpen(true)}
                className="mt-6 gap-2"
              >
                <Plus className="h-4 w-4" />
                Create Project
              </Button>
            </>
          )}
        </motion.div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project, index) => (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: index * 0.03 }}
              >
                <Card className="group relative overflow-hidden transition-all hover:shadow-card-hover">
                  <div className="p-6 flex flex-col h-full">
                    <div className="flex items-start justify-between">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 shrink-0">
                        <Code2 className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => {
                            setEditingProject(project);
                            setCreateOpen(true);
                          }}
                          className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-all"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => setDeletingProject(project)}
                          className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:text-destructive hover:bg-red-50 transition-all"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>

                    <div className="mt-4 flex-1 min-w-0">
                      <h3 className="font-semibold truncate text-foreground">
                        {project.project_name}
                      </h3>
                      {project.description && (
                        <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                          {project.description}
                        </p>
                      )}
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-[11px] font-medium text-primary">
                        <Code2 className="h-3 w-3" />
                        {project.language}
                      </span>
                      {project.framework && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-0.5 text-[11px] font-medium text-foreground">
                          <Globe className="h-3 w-3" />
                          {project.framework}
                        </span>
                      )}
                      {project.version && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground">
                          <Tag className="h-3 w-3" />
                          v{project.version}
                        </span>
                      )}
                    </div>

                    <div className="mt-3 pt-3 border-t border-border flex items-center gap-1 text-[11px] text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      {formatDate(project.created_at)}
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="gap-1"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                  (pageNum) => (
                    <Button
                      key={pageNum}
                      variant={pageNum === page ? "default" : "ghost"}
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={() => setPage(pageNum)}
                    >
                      {pageNum}
                    </Button>
                  ),
                )}
              </div>
              <Button
                variant="ghost"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="gap-1"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}

          <p className="text-center text-xs text-muted-foreground">
            Showing {projects.length} of {total} project{total !== 1 ? "s" : ""}
          </p>
        </>
      )}

      <CreateProjectDialog
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setEditingProject(null);
        }}
        onSubmit={editingProject ? handleUpdate : handleCreate}
        editProject={editingProject}
      />

      <DeleteProjectDialog
        open={deletingProject !== null}
        onClose={() => setDeletingProject(null)}
        onConfirm={handleDelete}
        projectName={deletingProject?.project_name ?? ""}
      />
    </div>
  );
}
