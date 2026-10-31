import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const memory = process.memoryUsage();
  const uptime = process.uptime();
  const nodeVersion = process.version;
  const env = process.env.NODE_ENV || "production";
  const isContainer = Boolean(
    process.env.NIRMAYA_CONTAINER ||
    process.env.DOCKER_CONTAINER ||
    process.env.HOSTNAME?.length === 12
  );

  const payload = {
    status: "healthy",
    service: "nirmaya-frontend",
    version: "0.1.0",
    environment: env,
    timestamp: new Date().toISOString(),
    uptimeSeconds: Math.round(uptime * 100) / 100,
    runtime: {
      engine: "nodejs",
      version: nodeVersion,
      platform: process.platform,
      arch: process.arch,
      pid: process.pid,
    },
    container: {
      isContainer,
      isStandalone: true,
      nonRootUid: 1001,
      nonRootGroup: "nodejs",
      nonRootUser: "nextjs",
    },
    memory: {
      rssMb: Math.round((memory.rss / (1024 * 1024)) * 10) / 10,
      heapTotalMb: Math.round((memory.heapTotal / (1024 * 1024)) * 10) / 10,
      heapUsedMb: Math.round((memory.heapUsed / (1024 * 1024)) * 10) / 10,
      externalMb: Math.round((memory.external / (1024 * 1024)) * 10) / 10,
    },
    caching: {
      staticCacheHeader: "public, max-age=31536000, immutable",
      targetFootprintMb: 145.0,
    },
  };

  return NextResponse.json(payload, {
    status: 200,
    headers: {
      "Cache-Control": "no-store, no-cache, must-revalidate",
      "X-Container-Service": "nirmaya-frontend",
      "X-Health-Status": "healthy",
    },
  });
}
