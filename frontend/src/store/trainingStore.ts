import { create } from 'zustand';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Exercise {
  id: string;
  name: string;
  category: string;
  prescription_type: string;
  load_level: string;
  protocol_id: string;
  protocol_name: string;
  protocol_description: string;
  sets: string;
  reps?: string;  // For KB_STRENGTH, BW_DYNAMIC, POWER_SWING
  hold_time?: string;  // For ISOMETRIC_HOLD
  time?: string;  // For CARRY_TIME, CRAWL_TIME
  rest: string;
  tempo?: string;
  notes?: string;
}

interface Session {
  id: string;
  timestamp: string;
  day_type: 'easy' | 'medium' | 'hard';
  priority_bucket: string;
  exercises: Exercise[];
  time_slot: string;
  equipment: string;
  week_mode: string;
}

interface UserState {
  id: string;
  next_priority_bucket: string;
  week_mode: 'A' | 'B';
  cooldown_counter: number;
  cooldown_override: boolean;  // Bypass cooldown for day type decisions
  power_last_used: string | null;
  last_hard_day: boolean;
  power_frequency: 'weekly' | 'fortnightly';
}

interface Questionnaire {
  feeling: 'bad' | 'ok' | 'great';
  sleep: 'bad' | 'good';
  pain: 'none' | 'present';
  time_available: '20-30' | '30-45' | '45-60';
  equipment: 'home' | 'minimal' | 'bodyweight';
}

interface TrainingStore {
  currentSession: Session | null;
  userState: UserState | null;
  lastQuestionnaire: Questionnaire | null;
  overrideBucket: string | null;
  setCurrentSession: (session: Session | null) => void;
  setUserState: (state: UserState) => void;
  setLastQuestionnaire: (q: Questionnaire) => void;
  setOverrideBucket: (bucket: string | null) => void;
  fetchUserState: () => Promise<void>;
  toggleCooldownOverride: () => Promise<void>;
}

export const useTrainingStore = create<TrainingStore>((set, get) => ({
  currentSession: null,
  userState: null,
  lastQuestionnaire: null,
  overrideBucket: null,
  
  setCurrentSession: (session) => set({ currentSession: session }),
  setUserState: (state) => set({ userState: state }),
  setLastQuestionnaire: (q) => set({ lastQuestionnaire: q }),
  setOverrideBucket: (bucket) => set({ overrideBucket: bucket }),
  
  fetchUserState: async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/state`);
      const data = await response.json();
      set({ userState: data });
    } catch (error) {
      console.error('Error fetching user state:', error);
    }
  },
  
  toggleCooldownOverride: async () => {
    const { userState } = get();
    if (!userState) return;
    
    try {
      const newValue = !userState.cooldown_override;
      const response = await fetch(`${BACKEND_URL}/api/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cooldown_override: newValue }),
      });
      const data = await response.json();
      set({ userState: data });
    } catch (error) {
      console.error('Error toggling cooldown override:', error);
    }
  },
}));
