/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react';
import type { PropsWithChildren } from 'react';
import type {
  DataProviderMode,
  FreshnessStatus,
  ProviderMode,
} from '../../lib/api/common.types';

export type AppShellSlots = {
  dataFreshness: FreshnessStatus | null;
  modelFreshness: FreshnessStatus | null;
  llmMode: ProviderMode | null;
  newsFreshness: FreshnessStatus | null;
  externalIndicatorsMode: DataProviderMode | null;
};

export const DEFAULT_APP_SHELL_SLOTS: AppShellSlots = {
  dataFreshness: null,
  modelFreshness: null,
  llmMode: null,
  newsFreshness: null,
  externalIndicatorsMode: null,
};

type AppShellSlotsContextValue = {
  slots: AppShellSlots;
  setSlots: (next: AppShellSlots) => void;
  patchSlots: (next: Partial<AppShellSlots>) => void;
  resetSlots: () => void;
};

const noop = () => {};

const AppShellSlotsContext = createContext<AppShellSlotsContextValue>({
  slots: DEFAULT_APP_SHELL_SLOTS,
  setSlots: noop,
  patchSlots: noop,
  resetSlots: noop,
});

type AppShellSlotsProviderProps = PropsWithChildren<{
  routeKey: string;
}>;

export function AppShellSlotsProvider({
  routeKey,
  children,
}: AppShellSlotsProviderProps) {
  const [slotsState, setSlotsState] = useState<{
    routeKey: string;
    slots: AppShellSlots;
  }>({ routeKey, slots: DEFAULT_APP_SHELL_SLOTS });
  const slots = slotsState.routeKey === routeKey ? slotsState.slots : DEFAULT_APP_SHELL_SLOTS;

  const setSlots = useCallback((next: AppShellSlots) => {
    setSlotsState({ routeKey, slots: next });
  }, [routeKey]);
  const patchSlots = useCallback(
    (next: Partial<AppShellSlots>) => {
      setSlotsState((prev) => {
        const base = prev.routeKey === routeKey ? prev.slots : DEFAULT_APP_SHELL_SLOTS;
        return { routeKey, slots: { ...base, ...next } };
      });
    },
    [routeKey],
  );
  const resetSlots = useCallback(() => {
    setSlotsState({ routeKey, slots: DEFAULT_APP_SHELL_SLOTS });
  }, [routeKey]);

  const value = useMemo<AppShellSlotsContextValue>(
    () => ({
      slots,
      setSlots,
      patchSlots,
      resetSlots,
    }),
    [patchSlots, resetSlots, setSlots, slots],
  );

  return (
    <AppShellSlotsContext.Provider value={value}>
      {children}
    </AppShellSlotsContext.Provider>
  );
}

export function useAppShellSlots(): AppShellSlotsContextValue {
  return useContext(AppShellSlotsContext);
}
