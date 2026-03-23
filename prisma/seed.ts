import { PrismaClient } from '@prisma/client'
import bcrypt from 'bcryptjs'

const db = new PrismaClient()

async function main() {
  console.log('Seeding Harbor database...')

  const password = 'Scan9455'
  const hash = await bcrypt.hash(password, 10)

  // Staff accounts - all use same dev password
  const staff = [
    { username: 'will', displayName: 'Will Scanland', role: 'admin', email: 'will@scanland.org' },
    { username: 'patricia', displayName: 'Patricia Scanland', role: 'admin', email: 'patricia@scanland.org' },
    { username: 'danny', displayName: 'Danny Patterson', role: 'staff', email: null },
  ]

  for (const s of staff) {
    await db.staff.upsert({
      where: { username: s.username },
      update: { passwordHash: hash },
      create: { username: s.username, passwordHash: hash, displayName: s.displayName, role: s.role, email: s.email },
    })
    console.log(`  Staff: ${s.username} (${s.role})`)
  }

  // Clients
  const clients = [
    { code: 'arc2214', name: 'Baldwin ARC', shortName: 'ARC' },
    { code: 'ccc9007', name: 'Community Connect CDC', shortName: 'CCC' },
    { code: 'csvr6048', name: 'CSVR', shortName: 'CSVR' },
    { code: 'loc8525', name: 'Light of the City', shortName: 'LOC' },
    { code: 'lov4600', name: 'Light of the Village', shortName: 'LOV' },
    { code: 'mla2051', name: 'Mercy Life of Alabama', shortName: 'MLA' },
    { code: 'stg7163', name: 'Striving for Greatness', shortName: 'STG' },
    { code: 'lth9396', name: 'The Lighthouse', shortName: 'LTH' },
    { code: 'stp9906', name: 'The Steeple', shortName: 'STP' },
    { code: 'tkg7869', name: 'Tuskegee', shortName: 'TKG' },
  ]

  for (const c of clients) {
    await db.client.upsert({
      where: { code: c.code },
      update: {},
      create: c,
    })
    console.log(`  Client: ${c.name}`)
  }

  // Aliases
  const ccc = await db.client.findFirst({ where: { name: 'Community Connect CDC' } })
  const arc = await db.client.findFirst({ where: { name: 'Baldwin ARC' } })

  if (ccc) {
    for (const alias of [
      { alias: "Carmita's Kitchen", aliasType: 'program' },
      { alias: 'Trinity Family Community Development Corporation', aliasType: 'related_org' },
      { alias: 'Trinity Family CDC', aliasType: 'related_org' },
      { alias: 'Trinity Family', aliasType: 'related_org' },
      { alias: 'CCCDC', aliasType: 'abbreviation' },
    ]) {
      const exists = await db.clientAlias.findFirst({ where: { alias: alias.alias, clientId: ccc.id } })
      if (!exists) await db.clientAlias.create({ data: { clientId: ccc.id, ...alias } })
    }
  }

  if (arc) {
    for (const alias of [
      { alias: 'ARC Baldwin County', aliasType: 'dba' },
      { alias: 'ARC', aliasType: 'abbreviation' },
    ]) {
      const exists = await db.clientAlias.findFirst({ where: { alias: alias.alias, clientId: arc.id } })
      if (!exists) await db.clientAlias.create({ data: { clientId: arc.id, ...alias } })
    }
  }

  console.log('\nAll dev passwords set to: Scan9455')
  console.log('To change passwords, edit prisma/seed.ts and re-run: npm run db:seed')
  console.log('\n✅ Database seeded!')
}

main()
  .catch(e => { console.error(e); process.exit(1) })
  .finally(() => db.$disconnect())
