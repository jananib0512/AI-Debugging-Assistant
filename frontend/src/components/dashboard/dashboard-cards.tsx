import { motion } from "framer-motion";
import {
  ArrowUpRight,
  Code2,
  FileCode,
  FolderKanban,
  Layers,
} from "lucide-react";
import { Link } from "react-router-dom";

interface CardItem {
  title: string;
  description: string;
  icon: React.ElementType;
  href: string;
}

const cards: CardItem[] = [
  {
    title: "My Projects",
    description: "View and manage your debugging projects",
    icon: FolderKanban,
    href: "/projects",
  },
  {
    title: "Recent Projects",
    description: "Quickly access your recently worked on projects",
    icon: Code2,
    href: "/projects",
  },
  {
    title: "Workspace",
    description: "Open your debugging workspace",
    icon: Layers,
    href: "/workspace",
  },
  {
    title: "Upload Project",
    description: "Upload a new project for analysis",
    icon: FileCode,
    href: "/upload",
  },
];

export function DashboardCards() {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {cards.map((card, index) => (
        <motion.div
          key={card.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.15 + index * 0.08 }}
        >
          <Link
            to={card.href}
            className="group block rounded-xl border border-border bg-card p-6 shadow-card transition-all hover:shadow-card-hover hover:border-border"
          >
            <div className="flex items-start justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
                <card.icon className="h-5 w-5 text-primary" />
              </div>
              <ArrowUpRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </div>
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-foreground">{card.title}</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                {card.description}
              </p>
            </div>
          </Link>
        </motion.div>
      ))}
    </div>
  );
}
