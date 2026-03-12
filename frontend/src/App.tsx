import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Layout from '@/components/Layout'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ProtectedRoute from '@/components/ProtectedRoute'

// Lazy-loaded pages for code splitting
const LandingPage = lazy(() => import('@/pages/LandingPage'))
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'))
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'))
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const CVAnalyzerPage = lazy(() => import('@/pages/CVAnalyzerPage'))
const JobBoardPage = lazy(() => import('@/pages/JobBoardPage'))
const ChatbotPage = lazy(() => import('@/pages/ChatbotPage'))
const ResourceHubPage = lazy(() => import('@/pages/ResourceHubPage'))
const ForumPage = lazy(() => import('@/pages/ForumPage'))
const AutoApplyPage = lazy(() => import('@/pages/AutoApplyPage'))
const NotificationsPage = lazy(() => import('@/pages/NotificationsPage'))
const MockInterviewPage = lazy(() => import('@/pages/MockInterviewPage'))
const AdminPanelPage = lazy(() => import('@/pages/AdminPanelPage'))
const ProfilePage = lazy(() => import('@/pages/ProfilePage'))

export default function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <AnimatePresence mode="wait">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="cv" element={<CVAnalyzerPage />} />
            <Route path="jobs" element={<JobBoardPage />} />
            <Route path="chat" element={<ChatbotPage />} />
            <Route path="resources" element={<ResourceHubPage />} />
            <Route path="forum" element={<ForumPage />} />
            <Route path="auto-apply" element={<AutoApplyPage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="interview" element={<MockInterviewPage />} />
            <Route path="profile" element={<ProfilePage />} />
            {/* Admin */}
            <Route
              path="admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AdminPanelPage />
                </ProtectedRoute>
              }
            />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </Suspense>
  )
}
