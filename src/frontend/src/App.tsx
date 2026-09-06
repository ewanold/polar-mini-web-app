import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { MappingsPage } from "./features/mappings/MappingsPage";
import { SettingsPage } from "./features/settings/SettingsPage";
import { TimelinePage } from "./features/timeline/TimelinePage";
import { TrainingPage } from "./features/training/TrainingPage";
import { ThemeProvider } from "./theme/ThemeProvider";
import { LanguageProvider } from "./i18n/LanguageProvider";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LanguageProvider><ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<Navigate replace to="/timeline" />} />
              <Route path="timeline" element={<TimelinePage />} />
              <Route path="training" element={<TrainingPage />} />
              <Route path="mappings" element={<MappingsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ThemeProvider></LanguageProvider>
    </QueryClientProvider>
  );
}
