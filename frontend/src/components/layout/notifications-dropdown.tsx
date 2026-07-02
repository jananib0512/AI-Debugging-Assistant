import { motion, AnimatePresence } from "framer-motion";
import { Inbox } from "lucide-react";

interface NotificationsDropdownProps {
  open: boolean;
  onClose: () => void;
}

export function NotificationsDropdown({ open, onClose }: NotificationsDropdownProps) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={onClose} />
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.96 }}
            transition={{ duration: 0.12 }}
            className="absolute right-0 top-full mt-2 w-80 overflow-hidden rounded-xl border border-border bg-popover shadow-dropdown z-50"
          >
            <div className="border-b border-border px-4 py-3">
              <p className="text-sm font-medium text-foreground">Notifications</p>
            </div>
            <div className="flex flex-col items-center justify-center py-12 px-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary mb-3">
                <Inbox className="h-5 w-5 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-foreground">No notifications yet</p>
              <p className="mt-0.5 text-xs text-muted-foreground text-center">
                We'll notify you when something arrives
              </p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
