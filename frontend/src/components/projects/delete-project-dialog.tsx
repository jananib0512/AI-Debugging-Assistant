import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, X } from "lucide-react";

import { Button } from "@/components/ui/button";

interface DeleteProjectDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  projectName: string;
}

export function DeleteProjectDialog({
  open,
  onClose,
  onConfirm,
  projectName,
}: DeleteProjectDialogProps) {
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
              className="w-full max-w-md rounded-xl border border-border bg-popover shadow-modal"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b border-border px-6 py-4">
                <h2 className="text-lg font-semibold text-foreground">Delete Project</h2>
                <button
                  onClick={onClose}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="p-6">
                <div className="flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-50">
                    <AlertTriangle className="h-5 w-5 text-destructive" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      Are you sure you want to delete this project?
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      <span className="font-medium text-foreground">
                        {projectName}
                      </span>{" "}
                      will be permanently deleted. This action cannot be
                      undone.
                    </p>
                  </div>
                </div>

                <div className="mt-6 flex justify-end gap-3">
                  <Button variant="ghost" onClick={onClose}>
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={async () => {
                      await onConfirm();
                      onClose();
                    }}
                  >
                    Delete project
                  </Button>
                </div>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
