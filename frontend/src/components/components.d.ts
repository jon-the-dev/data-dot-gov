// Type declarations for existing JSX components

declare module '@/components/Dashboard' {
  import type { ComponentType } from 'react';

  import type { DashboardData } from '@/types';

  interface DashboardProps {
    data: DashboardData;
  }

  const Dashboard: ComponentType<DashboardProps>;
  export default Dashboard;
}

declare module '@/components/PartyComparison' {
  import type { ComponentType } from 'react';

  import type { DashboardData } from '@/types';

  interface PartyComparisonProps {
    data: DashboardData;
  }

  const PartyComparison: ComponentType<PartyComparisonProps>;
  export default PartyComparison;
}

declare module '@/components/Members' {
  import type { ComponentType } from 'react';

  import type { DashboardData } from '@/types';

  interface MembersProps {
    data: DashboardData;
  }

  const Members: ComponentType<MembersProps>;
  export default Members;
}

declare module '@/components/BillDetail' {
  import type { ComponentType } from 'react';

  const BillDetail: ComponentType<{}>;
  export default BillDetail;
}
