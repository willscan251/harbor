import { NextAuthOptions } from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'
import bcrypt from 'bcryptjs'
import { db } from './db'

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      id: 'staff-login',
      name: 'Staff Login',
      credentials: {
        username: { label: 'Username', type: 'text' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) return null

        const staff = await db.staff.findUnique({
          where: { username: credentials.username },
        })

        if (!staff || !staff.passwordHash) return null

        const valid = await bcrypt.compare(credentials.password, staff.passwordHash)
        if (!valid) return null

        return {
          id: String(staff.id),
          name: staff.displayName,
          email: staff.email || `${staff.username}@harbor.local`,
          role: staff.role,
          username: staff.username,
        }
      },
    }),
    CredentialsProvider({
      id: 'client-login',
      name: 'Client Login',
      credentials: {
        code: { label: 'Client Code', type: 'text' },
      },
      async authorize(credentials) {
        if (!credentials?.code) return null

        const client = await db.client.findUnique({
          where: { code: credentials.code },
        })

        if (!client || client.status !== 'active') return null

        return {
          id: `client-${client.id}`,
          name: client.name,
          email: `client-${client.id}@harbor.local`,
          role: 'client',
          clientId: client.id,
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      // On initial sign-in, copy user fields to token
      if (user) {
        token.id = user.id
        token.name = user.name
        token.role = (user as any).role
        token.clientId = (user as any).clientId
        token.username = (user as any).username
      }
      return token
    },
    async session({ session, token }) {
      // Copy token fields to session
      if (session.user) {
        (session.user as any).id = token.id
        session.user.name = token.name as string
        (session.user as any).role = token.role
        (session.user as any).clientId = token.clientId
        (session.user as any).username = token.username
      }
      return session
    },
  },
  pages: {
    signIn: '/login',
  },
  session: { strategy: 'jwt' },
}
