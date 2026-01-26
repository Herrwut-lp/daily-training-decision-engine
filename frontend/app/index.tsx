import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Platform,
  Modal,
  Pressable,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTrainingStore } from '../src/store/trainingStore';

const BUCKET_ORDER = ['squat', 'pull', 'hinge', 'push'];

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

type Feeling = 'bad' | 'ok' | 'great';
type Sleep = 'bad' | 'good';
type Pain = 'none' | 'present';
type TimeAvailable = '20-30' | '30-45' | '45-60';
type Equipment = 'home' | 'minimal' | 'bodyweight';

interface QuestionnaireState {
  feeling: Feeling | null;
  sleep: Sleep | null;
  pain: Pain | null;
  time_available: TimeAvailable | null;
  equipment: Equipment | null;
}

export default function HomeScreen() {
  const router = useRouter();
  const { setCurrentSession, userState, fetchUserState } = useTrainingStore();
  const [loading, setLoading] = useState(false);
  const [questionnaire, setQuestionnaire] = useState<QuestionnaireState>({
    feeling: null,
    sleep: null,
    pain: null,
    time_available: null,
    equipment: null,
  });

  useEffect(() => {
    fetchUserState();
  }, []);

  const isComplete = () => {
    return (
      questionnaire.feeling &&
      questionnaire.sleep &&
      questionnaire.pain &&
      questionnaire.time_available &&
      questionnaire.equipment
    );
  };

  const generateSession = async () => {
    if (!isComplete()) return;
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(questionnaire),
      });
      const session = await response.json();
      setCurrentSession(session);
      // Save questionnaire for reroll
      useTrainingStore.setState({ lastQuestionnaire: questionnaire });
      router.push('/session');
    } catch (error) {
      console.error('Error generating session:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderOptionButton = (
    value: string,
    label: string,
    icon: string,
    selectedValue: string | null,
    onSelect: (val: any) => void,
    color?: string
  ) => {
    const isSelected = selectedValue === value;
    return (
      <TouchableOpacity
        style={[
          styles.optionButton,
          isSelected && styles.optionButtonSelected,
          isSelected && color && { borderColor: color, backgroundColor: color + '20' },
        ]}
        onPress={() => onSelect(value)}
        activeOpacity={0.7}
      >
        <Ionicons
          name={icon as any}
          size={28}
          color={isSelected ? (color || '#4ADE80') : '#666'}
        />
        <Text
          style={[
            styles.optionLabel,
            isSelected && { color: color || '#4ADE80' },
          ]}
        >
          {label}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Today's Training</Text>
          <TouchableOpacity
            style={styles.settingsButton}
            onPress={() => router.push('/settings')}
          >
            <Ionicons name="settings-outline" size={24} color="#888" />
          </TouchableOpacity>
        </View>

        {/* Status Tags */}
        <View style={styles.statusTags}>
          <View style={styles.statusTag}>
            <Text style={styles.statusTagText}>Week {userState?.week_mode || 'A'}</Text>
          </View>
          <View style={styles.statusTag}>
            <Ionicons name="arrow-forward" size={14} color="#888" />
            <Text style={styles.statusTagText}>
              {userState?.next_priority_bucket?.toUpperCase() || 'SQUAT'}
            </Text>
          </View>
          {(userState?.cooldown_counter || 0) > 0 && (
            <View style={[styles.statusTag, styles.cooldownTag]}>
              <Text style={styles.cooldownTagText}>COOLDOWN</Text>
            </View>
          )}
        </View>

        {/* Question 1: Feeling */}
        <View style={styles.questionSection}>
          <Text style={styles.questionTitle}>How are you feeling?</Text>
          <View style={styles.optionsRow}>
            {renderOptionButton('bad', 'Bad', 'sad-outline', questionnaire.feeling, (v) =>
              setQuestionnaire({ ...questionnaire, feeling: v }), '#EF4444'
            )}
            {renderOptionButton('ok', 'OK', 'remove-outline', questionnaire.feeling, (v) =>
              setQuestionnaire({ ...questionnaire, feeling: v }), '#F59E0B'
            )}
            {renderOptionButton('great', 'Great', 'happy-outline', questionnaire.feeling, (v) =>
              setQuestionnaire({ ...questionnaire, feeling: v }), '#4ADE80'
            )}
          </View>
        </View>

        {/* Question 2: Sleep */}
        <View style={styles.questionSection}>
          <Text style={styles.questionTitle}>Sleep quality?</Text>
          <View style={styles.optionsRow}>
            {renderOptionButton('bad', 'Bad', 'moon-outline', questionnaire.sleep, (v) =>
              setQuestionnaire({ ...questionnaire, sleep: v }), '#EF4444'
            )}
            {renderOptionButton('good', 'Good', 'moon', questionnaire.sleep, (v) =>
              setQuestionnaire({ ...questionnaire, sleep: v }), '#4ADE80'
            )}
          </View>
        </View>

        {/* Question 3: Pain */}
        <View style={styles.questionSection}>
          <Text style={styles.questionTitle}>Any pain?</Text>
          <View style={styles.optionsRow}>
            {renderOptionButton('none', 'None', 'checkmark-circle-outline', questionnaire.pain, (v) =>
              setQuestionnaire({ ...questionnaire, pain: v }), '#4ADE80'
            )}
            {renderOptionButton('present', 'Yes', 'alert-circle-outline', questionnaire.pain, (v) =>
              setQuestionnaire({ ...questionnaire, pain: v }), '#EF4444'
            )}
          </View>
        </View>

        {/* Question 4: Time */}
        <View style={styles.questionSection}>
          <Text style={styles.questionTitle}>Time available?</Text>
          <View style={styles.optionsRow}>
            {renderOptionButton('20-30', '20-30m', 'time-outline', questionnaire.time_available, (v) =>
              setQuestionnaire({ ...questionnaire, time_available: v }), '#3B82F6'
            )}
            {renderOptionButton('30-45', '30-45m', 'time-outline', questionnaire.time_available, (v) =>
              setQuestionnaire({ ...questionnaire, time_available: v }), '#3B82F6'
            )}
            {renderOptionButton('45-60', '45-60m', 'time-outline', questionnaire.time_available, (v) =>
              setQuestionnaire({ ...questionnaire, time_available: v }), '#3B82F6'
            )}
          </View>
        </View>

        {/* Question 5: Equipment */}
        <View style={styles.questionSection}>
          <Text style={styles.questionTitle}>Equipment?</Text>
          <View style={styles.optionsRow}>
            {renderOptionButton('home', 'Home', 'home-outline', questionnaire.equipment, (v) =>
              setQuestionnaire({ ...questionnaire, equipment: v }), '#8B5CF6'
            )}
            {renderOptionButton('minimal', 'Minimal', 'fitness-outline', questionnaire.equipment, (v) =>
              setQuestionnaire({ ...questionnaire, equipment: v }), '#8B5CF6'
            )}
            {renderOptionButton('bodyweight', 'BW', 'body-outline', questionnaire.equipment, (v) =>
              setQuestionnaire({ ...questionnaire, equipment: v }), '#8B5CF6'
            )}
          </View>
        </View>

        {/* Generate Button */}
        <TouchableOpacity
          style={[
            styles.generateButton,
            !isComplete() && styles.generateButtonDisabled,
          ]}
          onPress={generateSession}
          disabled={!isComplete() || loading}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color="#000" size="small" />
          ) : (
            <>
              <Ionicons name="flash" size={24} color="#000" />
              <Text style={styles.generateButtonText}>Generate Today</Text>
            </>
          )}
        </TouchableOpacity>
      </ScrollView>
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
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  settingsButton: {
    padding: 8,
  },
  statusTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 24,
  },
  statusTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 4,
  },
  statusTagText: {
    color: '#888',
    fontSize: 12,
    fontWeight: '600',
  },
  cooldownTag: {
    backgroundColor: '#EF444420',
    borderWidth: 1,
    borderColor: '#EF4444',
  },
  cooldownTagText: {
    color: '#EF4444',
    fontSize: 12,
    fontWeight: '600',
  },
  questionSection: {
    marginBottom: 24,
  },
  questionTitle: {
    color: '#999',
    fontSize: 14,
    marginBottom: 12,
    fontWeight: '500',
  },
  optionsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  optionButton: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
    gap: 8,
  },
  optionButtonSelected: {
    borderColor: '#4ADE80',
    backgroundColor: '#4ADE8010',
  },
  optionLabel: {
    color: '#666',
    fontSize: 13,
    fontWeight: '600',
  },
  generateButton: {
    backgroundColor: '#4ADE80',
    borderRadius: 16,
    paddingVertical: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginTop: 16,
  },
  generateButtonDisabled: {
    backgroundColor: '#333',
  },
  generateButtonText: {
    color: '#000',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
