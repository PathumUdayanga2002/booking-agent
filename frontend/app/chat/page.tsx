"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Header } from "@/components/Header";
import ChatBox from "@/components/ChatBox";

export default function ChatPage() {
  const { auth, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !auth) {
      router.push("/login");
    }
  }, [auth, isLoading, router]);

  if (isLoading || !auth) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <>
      <Header />
      <ChatBox />
    </>
  );
}
