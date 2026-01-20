import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Facilities from './pages/Facilities';
import FacilityDetail from './pages/FacilityDetail';
import Gaps from './pages/Gaps';
import Regulations from './pages/Regulations';
import Reports from './pages/Reports';
import Analysis from './pages/Analysis';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="facilities" element={<Facilities />} />
            <Route path="facilities/:id" element={<FacilityDetail />} />
            <Route path="gaps" element={<Gaps />} />
            <Route path="regulations" element={<Regulations />} />
            <Route path="reports" element={<Reports />} />
            <Route path="analysis" element={<Analysis />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
