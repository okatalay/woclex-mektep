import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './components/auth.jsx'
import { PageLoader } from './components/ui.jsx'
import Shell from './components/Shell.jsx'
import { JoinCodeEntry, JoinGuardian, JoinStudent, Login, RegisterTeacher } from './pages/AuthPages.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Classes from './pages/Classes.jsx'
import ClassDetail from './pages/ClassDetail.jsx'
import StudentDetail from './pages/StudentDetail.jsx'
import Children from './pages/Children.jsx'
import ChildDetail from './pages/ChildDetail.jsx'
import AssignmentDetail from './pages/AssignmentDetail.jsx'
import MyAssignments from './pages/MyAssignments.jsx'
import AssignmentSubmit from './pages/AssignmentSubmit.jsx'
import Messages from './pages/Messages.jsx'
import MessageThread from './pages/MessageThread.jsx'
import Announcements from './pages/Announcements.jsx'
import RouteDetail from './pages/RouteDetail.jsx'
import MyRoutes from './pages/MyRoutes.jsx'
import RouteJourney from './pages/RouteJourney.jsx'
import Library from './pages/Library.jsx'
import LibraryItemDetail from './pages/LibraryItemDetail.jsx'
import RouteTemplates from './pages/RouteTemplates.jsx'
import RouteTemplateDetail from './pages/RouteTemplateDetail.jsx'
import Curriculum from './pages/Curriculum.jsx'
import Attendance from './pages/Attendance.jsx'
import MyProgress from './pages/MyProgress.jsx'

function Protected({ children }) {
  const { user } = useAuth()
  if (user === undefined) return <PageLoader />
  if (!user) return <Navigate to="/giris" replace />
  return children
}

function PublicOnly({ children }) {
  const { user } = useAuth()
  if (user === undefined) return <PageLoader />
  if (user) return <Navigate to="/panel" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<PublicOnly><Login /></PublicOnly>} />
      <Route path="/giris" element={<PublicOnly><Login /></PublicOnly>} />
      <Route path="/kayit" element={<PublicOnly><RegisterTeacher /></PublicOnly>} />
      <Route path="/katil" element={<PublicOnly><JoinCodeEntry /></PublicOnly>} />
      <Route path="/katil/:code" element={<PublicOnly><JoinStudent /></PublicOnly>} />
      <Route path="/veli/:token" element={<PublicOnly><JoinGuardian /></PublicOnly>} />
      <Route path="/panel" element={<Protected><Shell /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path="siniflar" element={<Classes />} />
        <Route path="siniflar/:id" element={<ClassDetail />} />
        <Route path="siniflar/:id/ogrenciler/:studentId" element={<StudentDetail />} />
        <Route path="siniflar/:id/odevler/:assignmentId" element={<AssignmentDetail />} />
        <Route path="siniflar/:id/rotalar/:routeId" element={<RouteDetail />} />
        <Route path="cocuklarim" element={<Children />} />
        <Route path="cocuklarim/:studentId" element={<ChildDetail />} />
        <Route path="odevlerim" element={<MyAssignments />} />
        <Route path="odevlerim/:assignmentId" element={<AssignmentSubmit />} />
        <Route path="mesajlar" element={<Messages />} />
        <Route path="mesajlar/:id" element={<MessageThread />} />
        <Route path="duyurular" element={<Announcements />} />
        <Route path="rotalarim" element={<MyRoutes />} />
        <Route path="rotalarim/:routeId" element={<RouteJourney />} />
        <Route path="tilavet" element={<Library kind="tilavet" />} />
        <Route path="arsiv" element={<Library kind="arsiv" />} />
        <Route path="tilavet/:id" element={<LibraryItemDetail />} />
        <Route path="arsiv/:id" element={<LibraryItemDetail />} />
        <Route path="tilavet-arsivi/*" element={<Navigate to="/panel/tilavet" replace />} />
        <Route path="rota-arsivi" element={<RouteTemplates />} />
        <Route path="rota-arsivi/:id" element={<RouteTemplateDetail />} />
        <Route path="mufredat" element={<Curriculum />} />
        <Route path="siniflar/:id/yoklama" element={<Attendance />} />
        <Route path="gelisimim" element={<MyProgress />} />
        <Route path="*" element={<Navigate to="/panel" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
