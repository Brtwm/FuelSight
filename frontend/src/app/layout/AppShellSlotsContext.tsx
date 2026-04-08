import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
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
  const [slots, setSlotsState] = useState<AppShellSlots>(DEFAULT_APP_SHELL_SLOTS);
  const previousRouteRef = useRef(routeKey);
  const setSlots = useCallback((next: AppShellSlots) => {
    setSlotsState(next);
  }, []);
  const patchSlots = useCallback((next: Partial<AppShellSlots>) => {
    setSlotsState((prev) => ({ ...prev, ...next }));
  }, []);
  const resetSlots = useCallback(() => {
    setSlotsState(DEFAULT_APP_SHELL_SLOTS);
  }, []);

  useEffect(() => {
    if (previousRouteRef.current !== routeKey) {
      previousRouteRef.current = routeKey;
      resetSlots();
    }
  }, [resetSlots, routeKey]);

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
