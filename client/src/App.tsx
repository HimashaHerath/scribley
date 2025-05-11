import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from "./components/ui/sonner";
import DashboardLayout from "./components/layout/DashboardLayout";
import Dashboard from "./pages/Dashboard";
import Articles from "./pages/Articles";
import ArticleDetail from "./pages/ArticleDetail";
import CreateArticle from "./pages/CreateArticle";
import EditArticle from "./pages/EditArticle";
import Publications from "./pages/Publications";
import Settings from "./pages/Settings";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/dashboard"
          element={
            <DashboardLayout>
              <Dashboard />
            </DashboardLayout>
          }
        />
        <Route
          path="/articles"
          element={
            <DashboardLayout>
              <Articles />
            </DashboardLayout>
          }
        />
        <Route
          path="/articles/new"
          element={
            <DashboardLayout>
              <CreateArticle />
            </DashboardLayout>
          }
        />
        <Route
          path="/articles/:id/edit"
          element={
            <DashboardLayout>
              <EditArticle />
            </DashboardLayout>
          }
        />
        <Route
          path="/articles/:id"
          element={
            <DashboardLayout>
              <ArticleDetail />
            </DashboardLayout>
          }
        />
        <Route
          path="/publications"
          element={
            <DashboardLayout>
              <Publications />
            </DashboardLayout>
          }
        />
        <Route
          path="/settings"
          element={
            <DashboardLayout>
              <Settings />
            </DashboardLayout>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      <Toaster />
    </BrowserRouter>
  );
}

export default App;
