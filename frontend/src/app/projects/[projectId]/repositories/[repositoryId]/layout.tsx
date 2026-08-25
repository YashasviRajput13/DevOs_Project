"use client";
import { useParams } from "next/navigation";
import TopNav from "@/components/TopNav";
import RepoSidebar from "@/components/RepoSidebar";

export default function RepoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams<{ projectId: string; repositoryId: string }>();
  const projectId = Number(params?.projectId);
  const repositoryId = Number(params?.repositoryId);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", display: "flex", flexDirection: "column" }}>
      <TopNav projectId={projectId} repositoryId={repositoryId} />
      <div style={{ display: "flex", flex: 1, overflow: "hidden", height: "calc(100vh - 48px)" }}>
        <RepoSidebar projectId={projectId} repositoryId={repositoryId} />
        <main style={{ flex: 1, overflow: "auto" }}>
          {children}
        </main>
      </div>
    </div>
  );
}
