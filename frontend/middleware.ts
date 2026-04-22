/**
 * Next.js middleware — protects /dashboard routes
 * File: outreachx/frontend/middleware.ts  (root of frontend folder)
 * 
 * Redirects unauthenticated users to /login
 * Redirects logged-in users away from /login and /register
 */

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('outreachx_token')?.value
  const { pathname } = request.nextUrl

  const isProtected = pathname.startsWith('/dashboard')
  const isAuthPage  = pathname === '/login' || pathname === '/register'

  // Not logged in → redirect to login
  if (isProtected && !token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Already logged in → redirect away from auth pages
  if (isAuthPage && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/login', '/register'],
}