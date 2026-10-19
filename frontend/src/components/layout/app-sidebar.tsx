import { useLocation } from '@tanstack/react-router'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarRail,
} from '@/components/ui/sidebar'
import { DataDisclaimer } from '@/components/data-disclaimer'
import { AppTitle } from './app-title'
import { FOOTER_ITEMS, MENU_ITEMS } from './data/sidebar-data'
import { NavGroup, SidebarMenuLink } from './nav-group'

export function AppSidebar() {
  const href = useLocation({ select: (location) => location.href })

  return (
    <Sidebar collapsible='icon' variant='inset'>
      <SidebarHeader>
        <AppTitle />
      </SidebarHeader>
      <SidebarContent>
        <NavGroup title='Analysis' items={MENU_ITEMS} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          {FOOTER_ITEMS.map((item) => (
            <SidebarMenuLink key={item.title} item={item} href={href} />
          ))}
        </SidebarMenu>
        <DataDisclaimer />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
