'use client';

import Link from 'next/link';

export default function UnauthorizedPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full text-center">
        <h1 className="text-4xl font-bold text-red-600 mb-4">403</h1>
        <h2 className="text-2xl font-bold mb-4">Access Denied</h2>
        <p className="text-gray-600 mb-6">
          You don't have permission to access this resource.
        </p>
        <Link
          href="/dashboard"
          className="inline-block px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition"
        >
          Go to Dashboard
        </Link>
      </div>
    </div>
  );
}
