import Link from "next/link";
import Image from "next/image";

export default function GlobalNotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-12 bg-gray-50">
      <Image
        src="/404.png"
        width={200}
        height={200}
        alt="404 error illustration"
        className="mb-6"
        priority
      />

      <h1 className="mb-2 text-4xl font-bold text-gray-900">
        Page Not Found
      </h1>

      <p className="mb-8 text-lg text-gray-600 max-w-md text-center">
        The page you are looking for does not exist.
      </p>

      <Link
        href="/"
        className="flex items-center justify-center rounded-full bg-gray-900 px-8 py-2.5 text-lg font-medium text-white transition-all hover:bg-gray-800"
      >
        Go to Home
      </Link>
    </div>
  );
}
