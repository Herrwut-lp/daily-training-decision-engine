import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Switch,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTrainingStore } from '../src/store/trainingStore';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function SettingsScreen() {
  const router = useRouter();
  const { userState, fetchUserState } = useTrainingStore();
  const [loading, setLoading] = useState(false);
  const [benchmarks, setBenchmarks] = useState({
    press_bell_kg: '',
    press_reps: '',
    pushup_max: '',
    pullup_max: '',
    front_squat_bells_kg: '',
    front_squat_reps: '',
    hinge_bell_kg: '',
    hinge_reps: '',
    available_bells_minimal: '',
  });
  const [weekMode, setWeekMode] = useState<'A' | 'B'>('A');
  const [powerFrequency, setPowerFrequency] = useState<'weekly' | 'fortnightly'>('fortnightly');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [benchRes, stateRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/benchmarks`),
        fetch(`${BACKEND_URL}/api/state`),
      ]);
      const benchData = await benchRes.json();
      const stateData = await stateRes.json();

      setBenchmarks({
        press_bell_kg: benchData.press_bell_kg?.toString() || '',
        press_reps: benchData.press_reps?.toString() || '',
        pushup_max: benchData.pushup_max?.toString() || '',
        pullup_max: benchData.pullup_max?.toString() || '',
        front_squat_bells_kg: benchData.front_squat_bells_kg?.join(', ') || '',
        front_squat_reps: benchData.front_squat_reps?.toString() || '',
        hinge_bell_kg: benchData.hinge_bell_kg?.toString() || '',
        hinge_reps: benchData.hinge_reps?.toString() || '',
        available_bells_minimal: benchData.available_bells_minimal?.join(', ') || '16, 24, 28, 32',
      });
      setWeekMode(stateData.week_mode || 'A');
      setPowerFrequency(stateData.power_frequency || 'fortnightly');
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const saveBenchmarks = async () => {
    setLoading(true);
    try {
      const payload: any = {};
      
      if (benchmarks.press_bell_kg) payload.press_bell_kg = parseInt(benchmarks.press_bell_kg);
      if (benchmarks.press_reps) payload.press_reps = parseInt(benchmarks.press_reps);
      if (benchmarks.pushup_max) payload.pushup_max = parseInt(benchmarks.pushup_max);
      if (benchmarks.pullup_max) payload.pullup_max = parseInt(benchmarks.pullup_max);
      if (benchmarks.front_squat_bells_kg) {
        payload.front_squat_bells_kg = benchmarks.front_squat_bells_kg.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
      }
      if (benchmarks.front_squat_reps) payload.front_squat_reps = parseInt(benchmarks.front_squat_reps);
      if (benchmarks.hinge_bell_kg) payload.hinge_bell_kg = parseInt(benchmarks.hinge_bell_kg);
      if (benchmarks.hinge_reps) payload.hinge_reps = parseInt(benchmarks.hinge_reps);
      if (benchmarks.available_bells_minimal) {
        payload.available_bells_minimal = benchmarks.available_bells_minimal.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
      }

      await fetch(`${BACKEND_URL}/api/benchmarks`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      console.error('Error saving benchmarks:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setLoading(true);
    try {
      await fetch(`${BACKEND_URL}/api/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          week_mode: weekMode,
          power_frequency: powerFrequency,
        }),
      });
      fetchUserState();
    } catch (error) {
      console.error('Error saving settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAll = async () => {
    await Promise.all([saveBenchmarks(), saveSettings()]);
    router.back();
  };

  const renderInput = (
    label: string,
    value: string,
    key: keyof typeof benchmarks,
    placeholder: string,
    hint?: string
  ) => (
    <View style={styles.inputGroup}>
      <Text style={styles.inputLabel}>{label}</Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={(text) => setBenchmarks({ ...benchmarks, [key]: text })}
        placeholder={placeholder}
        placeholderTextColor="#444"
        keyboardType="numeric"
      />
      {hint && <Text style={styles.inputHint}>{hint}</Text>}
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Week Mode Toggle */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Training Mode</Text>
            <View style={styles.toggleRow}>
              <View>
                <Text style={styles.toggleLabel}>Week Mode</Text>
                <Text style={styles.toggleHint}>
                  A = Bilateral emphasis | B = Single-leg emphasis
                </Text>
              </View>
              <View style={styles.toggleButtons}>
                <TouchableOpacity
                  style={[
                    styles.toggleButton,
                    weekMode === 'A' && styles.toggleButtonActive,
                  ]}
                  onPress={() => setWeekMode('A')}
                >
                  <Text
                    style={[
                      styles.toggleButtonText,
                      weekMode === 'A' && styles.toggleButtonTextActive,
                    ]}
                  >
                    A
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.toggleButton,
                    weekMode === 'B' && styles.toggleButtonActive,
                  ]}
                  onPress={() => setWeekMode('B')}
                >
                  <Text
                    style={[
                      styles.toggleButtonText,
                      weekMode === 'B' && styles.toggleButtonTextActive,
                    ]}
                  >
                    B
                  </Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.toggleRow}>
              <View>
                <Text style={styles.toggleLabel}>Power Frequency</Text>
                <Text style={styles.toggleHint}>
                  How often swings can appear
                </Text>
              </View>
              <View style={styles.toggleButtons}>
                <TouchableOpacity
                  style={[
                    styles.toggleButtonWide,
                    powerFrequency === 'weekly' && styles.toggleButtonActive,
                  ]}
                  onPress={() => setPowerFrequency('weekly')}
                >
                  <Text
                    style={[
                      styles.toggleButtonText,
                      powerFrequency === 'weekly' && styles.toggleButtonTextActive,
                    ]}
                  >
                    Weekly
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.toggleButtonWide,
                    powerFrequency === 'fortnightly' && styles.toggleButtonActive,
                  ]}
                  onPress={() => setPowerFrequency('fortnightly')}
                >
                  <Text
                    style={[
                      styles.toggleButtonText,
                      powerFrequency === 'fortnightly' && styles.toggleButtonTextActive,
                    ]}
                  >
                    2 Weeks
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>

          {/* Benchmarks */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Benchmarks (Optional)</Text>
            <Text style={styles.sectionHint}>
              Set these to improve auto-loading. Leave blank for conservative defaults.
            </Text>

            <View style={styles.inputRow}>
              {renderInput('Press Bell (kg)', benchmarks.press_bell_kg, 'press_bell_kg', '24')}
              {renderInput('Press Reps', benchmarks.press_reps, 'press_reps', '5')}
            </View>

            <View style={styles.inputRow}>
              {renderInput('Push-up Max', benchmarks.pushup_max, 'pushup_max', '20')}
              {renderInput('Pull-up Max', benchmarks.pullup_max, 'pullup_max', '10')}
            </View>

            {renderInput(
              'Front Squat Bells (kg)',
              benchmarks.front_squat_bells_kg,
              'front_squat_bells_kg',
              '24, 24',
              'Comma separated: e.g. 24, 24'
            )}

            {renderInput(
              'Front Squat Reps',
              benchmarks.front_squat_reps,
              'front_squat_reps',
              '5'
            )}

            <View style={styles.inputRow}>
              {renderInput('Hinge Bell (kg)', benchmarks.hinge_bell_kg, 'hinge_bell_kg', '32')}
              {renderInput('Hinge Reps', benchmarks.hinge_reps, 'hinge_reps', '10')}
            </View>

            {renderInput(
              'Minimal Bells Available (kg)',
              benchmarks.available_bells_minimal,
              'available_bells_minimal',
              '16, 24, 28, 32',
              'What bells you have when minimal'
            )}
          </View>

          {/* Current State Info */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Current State</Text>
            <View style={styles.stateInfo}>
              <View style={styles.stateRow}>
                <Text style={styles.stateLabel}>Next Priority:</Text>
                <Text style={styles.stateValue}>
                  {userState?.next_priority_bucket?.toUpperCase() || 'SQUAT'}
                </Text>
              </View>
              <View style={styles.stateRow}>
                <Text style={styles.stateLabel}>Cooldown:</Text>
                <Text style={styles.stateValue}>
                  {userState?.cooldown_counter || 0} sessions
                </Text>
              </View>
            </View>
          </View>
        </ScrollView>

        {/* Save Button */}
        <View style={styles.footer}>
          <TouchableOpacity
            style={styles.saveButton}
            onPress={handleSaveAll}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#000" />
            ) : (
              <>
                <Ionicons name="checkmark" size={20} color="#000" />
                <Text style={styles.saveButtonText}>Save Settings</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 100,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  sectionHint: {
    color: '#666',
    fontSize: 13,
    marginBottom: 16,
  },
  toggleRow: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  toggleLabel: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 4,
  },
  toggleHint: {
    color: '#666',
    fontSize: 12,
    marginBottom: 12,
  },
  toggleButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  toggleButton: {
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#2a2a2a',
  },
  toggleButtonWide: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#2a2a2a',
  },
  toggleButtonActive: {
    backgroundColor: '#4ADE80',
  },
  toggleButtonText: {
    color: '#888',
    fontSize: 14,
    fontWeight: '600',
  },
  toggleButtonTextActive: {
    color: '#000',
  },
  inputGroup: {
    flex: 1,
    marginBottom: 12,
  },
  inputRow: {
    flexDirection: 'row',
    gap: 12,
  },
  inputLabel: {
    color: '#888',
    fontSize: 13,
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    fontSize: 15,
  },
  inputHint: {
    color: '#555',
    fontSize: 11,
    marginTop: 4,
  },
  stateInfo: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
  },
  stateRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  stateLabel: {
    color: '#666',
    fontSize: 14,
  },
  stateValue: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 16,
    paddingBottom: 32,
    backgroundColor: '#0a0a0a',
    borderTopWidth: 1,
    borderTopColor: '#1a1a1a',
  },
  saveButton: {
    backgroundColor: '#4ADE80',
    borderRadius: 12,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  saveButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
