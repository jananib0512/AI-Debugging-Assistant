import { AnimatePresence } from "framer-motion";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { RootLayout } from "@/components/layout/root-layout";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { LoginPage } from "@/pages/login-page";
import { RegisterPage } from "@/pages/register-page";
import { DashboardPage } from "@/pages/dashboard-page";
import { ProjectsPage } from "@/pages/projects-page";
import { WorkspacePage } from "@/pages/workspace-page";
import { ProjectOverviewPage } from "@/pages/project-overview-page";
import { WorkspaceValidationPage } from "@/pages/workspace-validation-page";
import { AnalysisReadinessPage } from "@/pages/analysis-readiness-page";
import { ProjectAnalyzerPage } from "@/pages/project-analyzer-page";
import { UploadPage } from "@/pages/upload-page";
import { ScanHistoryPage } from "@/pages/scan-history-page";
import { AiStatusPage } from "@/pages/ai-status-page";
import { SettingsPage } from "@/pages/settings-page";
import { ProfilePage } from "@/pages/profile-page";
import { AuthProvider } from "@/providers/auth-provider";

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<RootLayout />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/projects" element={<ProjectsPage />} />
                <Route path="/workspace" element={<WorkspacePage />} />
                <Route path="/workspace/:projectId" element={<WorkspacePage />} />
                <Route path="/projects/:projectId/overview" element={<ProjectOverviewPage />} />
                <Route path="/projects/:projectId/validation" element={<WorkspaceValidationPage />} />
                <Route path="/projects/:projectId/ready" element={<AnalysisReadinessPage />} />
                <Route path="/projects/:projectId/analyze" element={<ProjectAnalyzerPage />} />
                <Route path="/projects/:projectId/analyzer" element={<ProjectAnalyzerPage />} />
                <Route path="/upload" element={<UploadPage />} />
                <Route path="/scan-history" element={<ScanHistoryPage />} />
                <Route path="/ai-status" element={<AiStatusPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/profile" element={<ProfilePage />} />
              </Route>
            </Route>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AnimatePresence>
      </AuthProvider>
    </BrowserRouter>
  );
}
