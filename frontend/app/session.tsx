import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTrainingStore } from '../src/store/trainingStore';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

const getCategoryColor = (category: string) => {
  const colors: { [key: string]: string } = {
    squat: '#3B82F6',
    hinge: '#F59E0B',
    push: '#EF4444',
    pull: '#8B5CF6',
    carry: '#10B981',
    crawl: '#06B6D4',
  };
  return colors[category] || '#666';
};

const getDayTypeStyle = (dayType: string) => {
  switch (dayType) {
    case 'easy':
      return { bg: '#10B98120', border: '#10B981', text: '#10B981' };
    case 'medium':
      return { bg: '#F59E0B20', border: '#F59E0B', text: '#F59E0B' };
    case 'hard':
      return { bg: '#EF444420', border: '#EF4444', text: '#EF4444' };
    default:
      return { bg: '#33333320', border: '#333', text: '#888' };
  }
};

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
  reps?: string;
  hold_time?: string;
  time?: string;
  rest: string;
  tempo?: string;
  notes?: string;
}

export default function SessionScreen() {
  const router = useRouter();
  const { currentSession, setCurrentSession, lastQuestionnaire, setOverrideBucket } = useTrainingStore();
  const [loading, setLoading] = useState(false);
  const [swappingId, setSwappingId] = useState<string | null>(null);
  const [exercises, setExercises] = useState<Exercise[]>(currentSession?.exercises || []);
  
  // Protocol modal state
  const [protocolModalVisible, setProtocolModalVisible] = useState(false);
  const [selectedProtocol, setSelectedProtocol] = useState<{
    name: string;
    description: string;
  } | null>(null);

  if (!currentSession) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.emptyState}>
          <Ionicons name="barbell-outline" size={64} color="#333" />
          <Text style={styles.emptyText}>No session generated</Text>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Text style={styles.backButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const dayTypeStyle = getDayTypeStyle(currentSession.day_type);

  const handleReroll = async () => {
    if (!lastQuestionnaire) return;
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/reroll`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lastQuestionnaire),
      });
      const session = await response.json();
      setCurrentSession(session);
      setExercises(session.exercises);
    } catch (error) {
      console.error('Error rerolling session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSwap = async (exerciseId: string) => {
    setSwappingId(exerciseId);
    try {
      const response = await fetch(`${BACKEND_URL}/api/swap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSession.id,
          exercise_id: exerciseId,
          equipment: currentSession.equipment,
        }),
      });
      const newExercise = await response.json();
      
      const updatedExercises = exercises.map((ex) =>
        ex.id === exerciseId ? newExercise : ex
      );
      setExercises(updatedExercises);
    } catch (error) {
      console.error('Error swapping exercise:', error);
    } finally {
      setSwappingId(null);
    }
  };

  const handleComplete = async (feedback: 'good' | 'not_good') => {
    setLoading(true);
    try {
      await fetch(`${BACKEND_URL}/api/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSession.id,
          feedback: feedback,
        }),
      });
      setCurrentSession(null);
      setOverrideBucket(null); // Clear any manual focus override
      router.replace('/');
    } catch (error) {
      console.error('Error completing session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDiscard = () => {
    Alert.alert(
      'Discard Session?',
      'This will NOT count as a completed session. Your rotation and cooldown will stay the same.',
      [
        {
          text: 'Keep Session',
          style: 'cancel',
        },
        {
          text: 'Discard',
          style: 'destructive',
          onPress: () => {
            setCurrentSession(null);
            router.replace('/');
          },
        },
      ]
    );
  };

  const confirmComplete = () => {
    Alert.alert(
      'Session Complete?',
      'How was your training?',
      [
        {
          text: 'Not Good',
          style: 'destructive',
          onPress: () => handleComplete('not_good'),
        },
        {
          text: 'Good',
          onPress: () => handleComplete('good'),
        },
        {
          text: 'Cancel',
          style: 'cancel',
        },
      ]
    );
  };

  const showProtocolInfo = (exercise: Exercise) => {
    setSelectedProtocol({
      name: exercise.protocol_name,
      description: exercise.protocol_description,
    });
    setProtocolModalVisible(true);
  };

  // Helper to get the appropriate volume field based on prescription type
  const getVolumeDisplay = (exercise: Exercise) => {
    const prescriptionType = exercise.prescription_type;
    
    if (prescriptionType === 'ISOMETRIC_HOLD') {
      return {
        label: 'Hold',
        value: exercise.hold_time || '10-20s',
      };
    } else if (prescriptionType === 'CARRY_TIME' || prescriptionType === 'CRAWL_TIME') {
      return {
        label: 'Time',
        value: exercise.time || '30-60s',
      };
    } else {
      // KB_STRENGTH, BW_DYNAMIC, POWER_SWING
      return {
        label: 'Reps',
        value: exercise.reps || '5',
      };
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Protocol Info Modal */}
      <Modal
        visible={protocolModalVisible}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setProtocolModalVisible(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setProtocolModalVisible(false)}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Ionicons name="information-circle" size={24} color="#4ADE80" />
              <Text style={styles.modalTitle}>{selectedProtocol?.name}</Text>
            </View>
            <Text style={styles.modalDescription}>
              {selectedProtocol?.description}
            </Text>
            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setProtocolModalVisible(false)}
            >
              <Text style={styles.modalCloseText}>Got it</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleDiscard} style={styles.backArrow}>
          <Ionicons name="close" size={24} color="#888" />
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <Text style={styles.headerTitle}>Your Session</Text>
        </View>
        <TouchableOpacity onPress={handleDiscard} style={styles.discardButton}>
          <Text style={styles.discardText}>Discard</Text>
        </TouchableOpacity>
      </View>

      {/* Session Info Tags */}
      <View style={styles.sessionTags}>
        <View
          style={[
            styles.dayTypeTag,
            {
              backgroundColor: dayTypeStyle.bg,
              borderColor: dayTypeStyle.border,
            },
          ]}
        >
          <Text style={[styles.dayTypeText, { color: dayTypeStyle.text }]}>
            {currentSession.day_type.toUpperCase()}
          </Text>
        </View>
        <View style={styles.infoTag}>
          <Ionicons name="timer-outline" size={14} color="#888" />
          <Text style={styles.infoTagText}>{currentSession.time_slot}m</Text>
        </View>
        <View style={styles.infoTag}>
          <Ionicons name="fitness-outline" size={14} color="#888" />
          <Text style={styles.infoTagText}>{currentSession.equipment}</Text>
        </View>
        <View style={styles.infoTag}>
          <Ionicons name="arrow-forward" size={14} color="#888" />
          <Text style={styles.infoTagText}>
            {currentSession.priority_bucket}
          </Text>
        </View>
      </View>

      {/* Exercises List */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {exercises.map((exercise, index) => {
          const volumeDisplay = getVolumeDisplay(exercise);
          
          return (
            <View key={`${exercise.id}-${index}`} style={styles.exerciseCard}>
              <View style={styles.exerciseHeader}>
                <View
                  style={[
                    styles.categoryBadge,
                    { backgroundColor: getCategoryColor(exercise.category) + '20' },
                  ]}
                >
                  <Text
                    style={[
                      styles.categoryText,
                      { color: getCategoryColor(exercise.category) },
                    ]}
                  >
                    {exercise.category.toUpperCase()}
                  </Text>
                </View>
                {exercise.notes && (
                  <View style={styles.noteBadge}>
                    <Text style={styles.noteText}>{exercise.notes}</Text>
                  </View>
                )}
                <TouchableOpacity
                  style={styles.swapButton}
                  onPress={() => handleSwap(exercise.id)}
                  disabled={swappingId === exercise.id}
                >
                  {swappingId === exercise.id ? (
                    <ActivityIndicator size="small" color="#888" />
                  ) : (
                    <Ionicons name="swap-horizontal" size={20} color="#888" />
                  )}
                </TouchableOpacity>
              </View>

              <Text style={styles.exerciseName}>{exercise.name}</Text>

              <View style={styles.exerciseDetails}>
                <View style={styles.detailItem}>
                  <Text style={styles.detailLabel}>Load</Text>
                  <Text style={styles.detailValue}>{exercise.load_level}</Text>
                </View>
                <TouchableOpacity 
                  style={styles.detailItem}
                  onPress={() => showProtocolInfo(exercise)}
                  activeOpacity={0.7}
                >
                  <View style={styles.protocolLabelRow}>
                    <Text style={styles.detailLabel}>Protocol</Text>
                    <Ionicons name="information-circle-outline" size={12} color="#4ADE80" />
                  </View>
                  <Text style={[styles.detailValue, styles.protocolValue]}>
                    {exercise.protocol_name}
                  </Text>
                </TouchableOpacity>
              </View>

              <View style={styles.exerciseDetails}>
                <View style={styles.detailItem}>
                  <Text style={styles.detailLabel}>Sets</Text>
                  <Text style={styles.detailValue}>{exercise.sets}</Text>
                </View>
                <View style={styles.detailItem}>
                  <Text style={styles.detailLabel}>{volumeDisplay.label}</Text>
                  <Text style={styles.detailValue}>{volumeDisplay.value}</Text>
                </View>
                <View style={styles.detailItem}>
                  <Text style={styles.detailLabel}>Rest</Text>
                  <Text style={styles.detailValue}>{exercise.rest}</Text>
                </View>
              </View>
              
              {exercise.tempo && (
                <View style={styles.tempoRow}>
                  <Text style={styles.tempoLabel}>Tempo:</Text>
                  <Text style={styles.tempoValue}>{exercise.tempo}</Text>
                </View>
              )}
            </View>
          );
        })}
      </ScrollView>

      {/* Action Buttons */}
      <View style={styles.actionBar}>
        <TouchableOpacity
          style={styles.rerollButton}
          onPress={handleReroll}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <>
              <Ionicons name="refresh" size={20} color="#fff" />
              <Text style={styles.rerollText}>Reroll</Text>
            </>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.doneButton}
          onPress={confirmComplete}
          disabled={loading}
        >
          <Ionicons name="checkmark-circle" size={24} color="#000" />
          <Text style={styles.doneText}>Done</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  emptyText: {
    color: '#666',
    fontSize: 16,
  },
  backButton: {
    backgroundColor: '#1a1a1a',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backArrow: {
    padding: 4,
  },
  headerTitleContainer: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  discardButton: {
    padding: 4,
  },
  discardText: {
    color: '#EF4444',
    fontSize: 14,
    fontWeight: '500',
  },
  sessionTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  dayTypeTag: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
  },
  dayTypeText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  infoTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 4,
  },
  infoTagText: {
    color: '#888',
    fontSize: 12,
    fontWeight: '500',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 100,
  },
  exerciseCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  exerciseHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 8,
  },
  categoryBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  categoryText: {
    fontSize: 11,
    fontWeight: 'bold',
  },
  noteBadge: {
    backgroundColor: '#4ADE8020',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  noteText: {
    color: '#4ADE80',
    fontSize: 10,
    fontWeight: '600',
  },
  swapButton: {
    marginLeft: 'auto',
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#2a2a2a',
  },
  exerciseName: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  exerciseDetails: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 8,
  },
  detailItem: {
    flex: 1,
  },
  detailLabel: {
    color: '#666',
    fontSize: 11,
    marginBottom: 2,
  },
  detailValue: {
    color: '#ccc',
    fontSize: 14,
    fontWeight: '500',
  },
  protocolLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 2,
  },
  protocolValue: {
    color: '#4ADE80',
    textDecorationLine: 'underline',
  },
  tempoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 4,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#2a2a2a',
  },
  tempoLabel: {
    color: '#666',
    fontSize: 11,
  },
  tempoValue: {
    color: '#F59E0B',
    fontSize: 13,
    fontWeight: '600',
  },
  actionBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    padding: 16,
    paddingBottom: 32,
    backgroundColor: '#0a0a0a',
    borderTopWidth: 1,
    borderTopColor: '#1a1a1a',
    gap: 12,
  },
  rerollButton: {
    flex: 1,
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  rerollText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  doneButton: {
    flex: 2,
    backgroundColor: '#4ADE80',
    borderRadius: 12,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  doneText: {
    color: '#000',
    fontSize: 16,
    fontWeight: 'bold',
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    width: '100%',
    maxWidth: 340,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 12,
  },
  modalTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    flex: 1,
  },
  modalDescription: {
    color: '#aaa',
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 20,
  },
  modalCloseButton: {
    backgroundColor: '#4ADE80',
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
  },
  modalCloseText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '600',
  },
});
