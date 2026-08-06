"use client";

import { BackLink, Card, SkeletonInput, SkeletonLabel, SkeletonTitle } from "@/components";

export default function LoginProviderPageSkeleton() {
  return (
    <div>
      <div className="flex items-center justify-between gap-4 mb-6">
        <SkeletonTitle />
      </div>
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-1.5">
              <SkeletonLabel />
              <SkeletonInput />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
