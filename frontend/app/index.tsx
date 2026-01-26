import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Modal,
  Pressable,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTrainingStore } from '../src/store/trainingStore';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
const BUCKET_ORDER = ['squat', 'pull', 'hinge', 'push'];

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
  const { setCurrentSession, userState, fetchUserState, setOverrideBucket, overrideBucket, toggleCooldownOverride } = useTrainingStore();
  const [loading, setLoading] = useState(false);
  const [showCooldownModal, setShowCooldownModal] = useState(false);
  const [showFocusModal, setShowFocusModal] = useState(false);
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

  const currentBucket = overrideBucket || userState?.next_priority_bucket || 'squat';

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
      const payload = {
        ...questionnaire,
        override_bucket: overrideBucket || undefined,
      };
      const response = await fetch(`${BACKEND_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const session = await response.json();
      setCurrentSession(session);
      useTrainingStore.setState({ lastQuestionnaire: questionnaire });
      router.push('/session');
    } catch (error) {
      console.error('Error generating session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBucketSelect = (bucket: string) => {
    if (bucket === userState?.next_priority_bucket) {
      setOverrideBucket(null); // Reset to auto
    } else {
      setOverrideBucket(bucket);
    }
    setShowFocusModal(false);
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
          
          {/* Focus/Priority Bucket - Tappable */}
          <TouchableOpacity 
            style={[
              styles.statusTag, 
              styles.focusTag,
              overrideBucket && styles.focusTagOverride
            ]}
            onPress={() => setShowFocusModal(true)}
            activeOpacity={0.7}
          >
            <Ionicons name="arrow-forward" size={14} color={overrideBucket ? '#3B82F6' : '#888'} />
            <Text style={[
              styles.statusTagText,
              overrideBucket && styles.focusTagTextOverride
            ]}>
              {currentBucket.toUpperCase()}
            </Text>
            <Ionicons name="chevron-down" size={12} color={overrideBucket ? '#3B82F6' : '#666'} />
          </TouchableOpacity>
          
          {/* Cooldown - Tappable */}
          {(userState?.cooldown_counter || 0) > 0 && (
            <TouchableOpacity 
              style={[
                styles.statusTag, 
                styles.cooldownTag,
                userState?.cooldown_override && styles.cooldownTagOverride
              ]}
              onPress={() => setShowCooldownModal(true)}
              activeOpacity={0.7}
            >
              <Text style={[
                styles.cooldownTagText,
                userState?.cooldown_override && styles.cooldownTagTextOverride
              ]}>
                {userState?.cooldown_override ? 'OVERRIDE ON' : `COOLDOWN (${userState?.cooldown_counter})`}
              </Text>
              <Ionicons 
                name={userState?.cooldown_override ? "flash" : "help-circle"} 
                size={14} 
                color={userState?.cooldown_override ? "#F59E0B" : "#EF4444"} 
              />
            </TouchableOpacity>
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

      {/* Cooldown Explanation Modal */}
      <Modal
        visible={showCooldownModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowCooldownModal(false)}
      >
        <Pressable 
          style={styles.modalOverlay}
          onPress={() => setShowCooldownModal(false)}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Ionicons name="snow-outline" size={28} color="#EF4444" />
              <Text style={styles.modalTitle}>Cooldown Mode</Text>
            </View>
            
            <Text style={styles.modalText}>
              Your body needs recovery. Cooldown is active for{' '}
              <Text style={styles.modalHighlight}>{userState?.cooldown_counter} more session(s)</Text>.
            </Text>
            
            {/* Override Toggle */}
            <TouchableOpacity
              style={[
                styles.overrideToggle,
                userState?.cooldown_override && styles.overrideToggleOn
              ]}
              onPress={() => {
                toggleCooldownOverride();
              }}
            >
              <View style={styles.overrideToggleContent}>
                <Ionicons 
                  name={userState?.cooldown_override ? "flash" : "flash-outline"} 
                  size={20} 
                  color={userState?.cooldown_override ? "#F59E0B" : "#888"} 
                />
                <View style={styles.overrideToggleTextContainer}>
                  <Text style={[
                    styles.overrideToggleTitle,
                    userState?.cooldown_override && styles.overrideToggleTitleOn
                  ]}>
                    Override: {userState?.cooldown_override ? 'ON' : 'OFF'}
                  </Text>
                  <Text style={styles.overrideToggleSubtext}>
                    {userState?.cooldown_override 
                      ? 'Day type ignores cooldown counter'
                      : 'Tap to bypass cooldown for testing'
                    }
                  </Text>
                </View>
                <View style={[
                  styles.overrideIndicator,
                  userState?.cooldown_override && styles.overrideIndicatorOn
                ]}>
                  <View style={[
                    styles.overrideIndicatorDot,
                    userState?.cooldown_override && styles.overrideIndicatorDotOn
                  ]} />
                </View>
              </View>
            </TouchableOpacity>
            
            <View style={styles.modalSection}>
              <Text style={styles.modalSubtitle}>What it does:</Text>
              <Text style={styles.modalBullet}>• Forces EASY day type regardless of how you feel</Text>
              <Text style={styles.modalBullet}>• Reduces volume and intensity automatically</Text>
              <Text style={styles.modalBullet}>• No power exercises (swings) allowed</Text>
            </View>
            
            <View style={styles.modalSection}>
              <Text style={styles.modalSubtitle}>Triggered by:</Text>
              <Text style={styles.modalBullet}>• Answering "Bad" to feeling or sleep</Text>
              <Text style={styles.modalBullet}>• Indicating pain is present</Text>
              <Text style={styles.modalBullet}>• Marking a session as "Not Good"</Text>
            </View>
            
            {userState?.cooldown_override && (
              <Text style={styles.modalWarning}>
                Override auto-resets when a real cooldown trigger happens.
              </Text>
            )}
            
            <Text style={styles.modalFooter}>
              Completes 1 session = cooldown decreases by 1
            </Text>
            
            <TouchableOpacity
              style={styles.modalButton}
              onPress={() => setShowCooldownModal(false)}
            >
              <Text style={styles.modalButtonText}>Got it</Text>
            </TouchableOpacity>
          </View>
        </Pressable>
      </Modal>

      {/* Focus Selection Modal */}
      <Modal
        visible={showFocusModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowFocusModal(false)}
      >
        <Pressable 
          style={styles.modalOverlay}
          onPress={() => setShowFocusModal(false)}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Ionicons name="fitness-outline" size={28} color="#3B82F6" />
              <Text style={styles.modalTitle}>Today's Focus</Text>
            </View>
            
            <Text style={styles.modalText}>
              Choose which movement pattern to prioritize. The first exercise will be from this category.
            </Text>
            
            <View style={styles.focusOptions}>
              {BUCKET_ORDER.map((bucket) => {
                const isAuto = bucket === userState?.next_priority_bucket;
                const isSelected = bucket === currentBucket;
                return (
                  <TouchableOpacity
                    key={bucket}
                    style={[
                      styles.focusOption,
                      isSelected && styles.focusOptionSelected,
                    ]}
                    onPress={() => handleBucketSelect(bucket)}
                  >
                    <Text style={[
                      styles.focusOptionText,
                      isSelected && styles.focusOptionTextSelected,
                    ]}>
                      {bucket.toUpperCase()}
                    </Text>
                    {isAuto && (
                      <Text style={styles.focusOptionAuto}>auto</Text>
                    )}
                  </TouchableOpacity>
                );
              })}
            </View>
            
            {overrideBucket && (
              <TouchableOpacity
                style={styles.resetButton}
                onPress={() => {
                  setOverrideBucket(null);
                  setShowFocusModal(false);
                }}
              >
                <Ionicons name="refresh" size={16} color="#888" />
                <Text style={styles.resetButtonText}>Reset to auto rotation</Text>
              </TouchableOpacity>
            )}
            
            <Text style={styles.modalFooter}>
              Auto rotation: squat → pull → hinge → push
            </Text>
          </View>
        </Pressable>
      </Modal>
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
  focusTag: {
    borderWidth: 1,
    borderColor: 'transparent',
  },
  focusTagOverride: {
    borderColor: '#3B82F6',
    backgroundColor: '#3B82F620',
  },
  focusTagTextOverride: {
    color: '#3B82F6',
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
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderRadius: 20,
    padding: 24,
    width: '100%',
    maxWidth: 360,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  modalTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  modalText: {
    color: '#aaa',
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 16,
  },
  modalHighlight: {
    color: '#EF4444',
    fontWeight: '600',
  },
  modalSection: {
    marginBottom: 16,
  },
  modalSubtitle: {
    color: '#888',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 8,
  },
  modalBullet: {
    color: '#ccc',
    fontSize: 14,
    lineHeight: 22,
    paddingLeft: 4,
  },
  modalFooter: {
    color: '#666',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 16,
  },
  modalButton: {
    backgroundColor: '#333',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  modalButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  focusOptions: {
    gap: 10,
    marginBottom: 16,
  },
  focusOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  focusOptionSelected: {
    borderColor: '#3B82F6',
    backgroundColor: '#3B82F620',
  },
  focusOptionText: {
    color: '#888',
    fontSize: 16,
    fontWeight: '600',
  },
  focusOptionTextSelected: {
    color: '#3B82F6',
  },
  focusOptionAuto: {
    color: '#4ADE80',
    fontSize: 12,
    fontWeight: '500',
  },
  resetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
  },
  resetButtonText: {
    color: '#888',
    fontSize: 14,
  },
});
