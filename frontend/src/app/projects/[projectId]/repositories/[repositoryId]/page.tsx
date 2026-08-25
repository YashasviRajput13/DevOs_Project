"use client";
import { useParams } from "next/navigation";
import { redirect } from "next/navigation";
import { useEffect } from "react";

export default function RepoIndex() {
  const { projectId, repositoryId } = useParams<{ projectId: string; repositoryId: string }>();
  useEffect(() => {
    window.location.href = `/projects/${projectId}/repositories/${repositoryId}/overview`;
  }, []);
  return null;
}
