import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Modal,
  Alert,
  ActivityIndicator,
  Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'https://training-program.barney-lab.xyz';

interface Exercise {
  id: string;
  name: string;
  category: string;
  equipment: string[];
  bilateral: boolean;
  is_anchor: boolean;
  prescription_type: string;
  is_power: boolean;
  custom_protocols?: string[];
}

interface Protocol {
  id: string;
  name: string;
  prescription_type: string;
  description_short: string;
  example?: string;
  sets: string;
  reps?: string;
  hold_time?: string;
  time?: string;
  rest: string;
  tempo?: string;
  is_easy_day: boolean;
}

const CATEGORIES = ['squat', 'hinge', 'push', 'pull', 'carry', 'crawl'];
const EQUIPMENT_OPTIONS = ['home', 'minimal', 'bodyweight'];
const PRESCRIPTION_TYPES = ['KB_STRENGTH', 'BW_DYNAMIC', 'ISOMETRIC_HOLD', 'CARRY_TIME', 'CRAWL_TIME', 'POWER_SWING'];

export default function AdminScreen() {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'exercises' | 'protocols'>('exercises');
  
  // Data
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [protocols, setProtocols] = useState<Protocol[]>([]);
  
  // Modal states
  const [showExerciseModal, setShowExerciseModal] = useState(false);
  const [showProtocolModal, setShowProtocolModal] = useState(false);
  const [editingExercise, setEditingExercise] = useState<Exercise | null>(null);
  const [editingProtocol, setEditingProtocol] = useState<Protocol | null>(null);
  
  // Form states for exercise
  const [exerciseForm, setExerciseForm] = useState({
    id: '',
    name: '',
    category: 'squat',
    equipment: ['home'],
    bilateral: true,
    is_anchor: false,
    prescription_type: 'KB_STRENGTH',
    is_power: false,
  });
  
  // Form states for protocol
  const [protocolForm, setProtocolForm] = useState({
    id: '',
    name: '',
    prescription_type: 'KB_STRENGTH',
    description_short: '',
    example: '',
    sets: '3-5',
    reps: '',
    hold_time: '',
    time: '',
    rest: '60s',
    tempo: '',
    is_easy_day: false,
  });

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (isLoggedIn && token) {
      fetchData();
    }
  }, [isLoggedIn, token]);

  const checkAuth = async () => {
    try {
      const savedToken = await AsyncStorage.getItem('admin_token');
      if (savedToken) {
        const response = await fetch(`${BACKEND_URL}/api/admin/verify`, {
          headers: { 'X-Admin-Token': savedToken }
        });
        if (response.ok) {
          setToken(savedToken);
          setIsLoggedIn(true);
        } else {
          await AsyncStorage.removeItem('admin_token');
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      
      if (response.ok) {
        const data = await response.json();
        await AsyncStorage.setItem('admin_token', data.token);
        setToken(data.token);
        setIsLoggedIn(true);
        setPassword('');
      } else {
        Alert.alert('Error', 'Invalid password');
      }
    } catch (error) {
      Alert.alert('Error', 'Login failed');
    }
  };

  const handleLogout = async () => {
    await AsyncStorage.removeItem('admin_token');
    setToken(null);
    setIsLoggedIn(false);
  };

  const fetchData = async () => {
    try {
      const [exercisesRes, protocolsRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/exercises`),
        fetch(`${BACKEND_URL}/api/protocols`),
      ]);
      
      setExercises(await exercisesRes.json());
      setProtocols(await protocolsRes.json());
    } catch (error) {
      console.error('Fetch failed:', error);
    }
  };

  // Exercise CRUD
  const openExerciseModal = (exercise?: Exercise) => {
    if (exercise) {
      setEditingExercise(exercise);
      setExerciseForm({
        id: exercise.id,
        name: exercise.name,
        category: exercise.category,
        equipment: exercise.equipment,
        bilateral: exercise.bilateral,
        is_anchor: exercise.is_anchor,
        prescription_type: exercise.prescription_type,
        is_power: exercise.is_power,
      });
    } else {
      setEditingExercise(null);
      setExerciseForm({
        id: '',
        name: '',
        category: 'squat',
        equipment: ['home'],
        bilateral: true,
        is_anchor: false,
        prescription_type: 'KB_STRENGTH',
        is_power: false,
      });
    }
    setShowExerciseModal(true);
  };

  const saveExercise = async () => {
    try {
      const url = editingExercise 
        ? `${BACKEND_URL}/api/admin/exercises/${editingExercise.id}`
        : `${BACKEND_URL}/api/admin/exercises`;
      
      const response = await fetch(url, {
        method: editingExercise ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': token || '',
        },
        body: JSON.stringify(exerciseForm),
      });
      
      if (response.ok) {
        setShowExerciseModal(false);
        fetchData();
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Save failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Save failed');
    }
  };

  const deleteExercise = async (exerciseId: string) => {
    Alert.alert('Delete Exercise', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            const response = await fetch(`${BACKEND_URL}/api/admin/exercises/${exerciseId}`, {
              method: 'DELETE',
              headers: { 'X-Admin-Token': token || '' },
            });
            if (response.ok) {
              fetchData();
            }
          } catch (error) {
            Alert.alert('Error', 'Delete failed');
          }
        },
      },
    ]);
  };

  // Protocol CRUD
  const openProtocolModal = (protocol?: Protocol) => {
    if (protocol) {
      setEditingProtocol(protocol);
      setProtocolForm({
        id: protocol.id,
        name: protocol.name,
        prescription_type: protocol.prescription_type,
        description_short: protocol.description_short,
        example: protocol.example || '',
        sets: protocol.sets,
        reps: protocol.reps || '',
        hold_time: protocol.hold_time || '',
        time: protocol.time || '',
        rest: protocol.rest,
        tempo: protocol.tempo || '',
        is_easy_day: protocol.is_easy_day,
      });
    } else {
      setEditingProtocol(null);
      setProtocolForm({
        id: '',
        name: '',
        prescription_type: 'KB_STRENGTH',
        description_short: '',
        example: '',
        sets: '3-5',
        reps: '',
        hold_time: '',
        time: '',
        rest: '60s',
        tempo: '',
        is_easy_day: false,
      });
    }
    setShowProtocolModal(true);
  };

  const saveProtocol = async () => {
    try {
      const url = editingProtocol 
        ? `${BACKEND_URL}/api/admin/protocols/${editingProtocol.id}`
        : `${BACKEND_URL}/api/admin/protocols`;
      
      const response = await fetch(url, {
        method: editingProtocol ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': token || '',
        },
        body: JSON.stringify(protocolForm),
      });
      
      if (response.ok) {
        setShowProtocolModal(false);
        fetchData();
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Save failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Save failed');
    }
  };

  const deleteProtocol = async (protocolId: string) => {
    Alert.alert('Delete Protocol', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            const response = await fetch(`${BACKEND_URL}/api/admin/protocols/${protocolId}`, {
              method: 'DELETE',
              headers: { 'X-Admin-Token': token || '' },
            });
            if (response.ok) {
              fetchData();
            }
          } catch (error) {
            Alert.alert('Error', 'Delete failed');
          }
        },
      },
    ]);
  };

  const toggleEquipment = (equip: string) => {
    if (exerciseForm.equipment.includes(equip)) {
      if (exerciseForm.equipment.length > 1) {
        setExerciseForm({
          ...exerciseForm,
          equipment: exerciseForm.equipment.filter(e => e !== equip),
        });
      }
    } else {
      setExerciseForm({
        ...exerciseForm,
        equipment: [...exerciseForm.equipment, equip],
      });
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#4ADE80" />
      </SafeAreaView>
    );
  }

  // Login Screen
  if (!isLoggedIn) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loginContainer}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color="#888" />
          </TouchableOpacity>
          
          <Ionicons name="lock-closed" size={64} color="#4ADE80" style={{ marginBottom: 24 }} />
          <Text style={styles.loginTitle}>Admin Access</Text>
          <Text style={styles.loginSubtitle}>Enter password to manage exercises and protocols</Text>
          
          <TextInput
            style={styles.passwordInput}
            placeholder="Password"
            placeholderTextColor="#666"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
            autoCapitalize="none"
          />
          
          <TouchableOpacity style={styles.loginButton} onPress={handleLogin}>
            <Text style={styles.loginButtonText}>Login</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Admin Dashboard
  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#888" />
        </TouchableOpacity>
        <Text style={styles.title}>Admin Panel</Text>
        <TouchableOpacity onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={24} color="#EF4444" />
        </TouchableOpacity>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'exercises' && styles.tabActive]}
          onPress={() => setActiveTab('exercises')}
        >
          <Text style={[styles.tabText, activeTab === 'exercises' && styles.tabTextActive]}>
            Exercises ({exercises.length})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'protocols' && styles.tabActive]}
          onPress={() => setActiveTab('protocols')}
        >
          <Text style={[styles.tabText, activeTab === 'protocols' && styles.tabTextActive]}>
            Protocols ({protocols.length})
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {activeTab === 'exercises' ? (
          <>
            <TouchableOpacity style={styles.addButton} onPress={() => openExerciseModal()}>
              <Ionicons name="add-circle" size={24} color="#4ADE80" />
              <Text style={styles.addButtonText}>Add Exercise</Text>
            </TouchableOpacity>

            {CATEGORIES.map(category => {
              const categoryExercises = exercises.filter(e => e.category === category);
              if (categoryExercises.length === 0) return null;
              return (
                <View key={category} style={styles.categorySection}>
                  <Text style={styles.categoryTitle}>{category.toUpperCase()}</Text>
                  {categoryExercises.map(exercise => (
                    <View key={exercise.id} style={styles.itemCard}>
                      <View style={styles.itemInfo}>
                        <Text style={styles.itemName}>{exercise.name}</Text>
                        <Text style={styles.itemMeta}>
                          {exercise.prescription_type} • {exercise.equipment.join(', ')}
                          {exercise.is_anchor && ' • ⭐ Anchor'}
                          {exercise.is_power && ' • ⚡ Power'}
                        </Text>
                      </View>
                      <View style={styles.itemActions}>
                        <TouchableOpacity onPress={() => openExerciseModal(exercise)}>
                          <Ionicons name="pencil" size={20} color="#3B82F6" />
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => deleteExercise(exercise.id)}>
                          <Ionicons name="trash" size={20} color="#EF4444" />
                        </TouchableOpacity>
                      </View>
                    </View>
                  ))}
                </View>
              );
            })}
          </>
        ) : (
          <>
            <TouchableOpacity style={styles.addButton} onPress={() => openProtocolModal()}>
              <Ionicons name="add-circle" size={24} color="#4ADE80" />
              <Text style={styles.addButtonText}>Add Protocol</Text>
            </TouchableOpacity>

            {PRESCRIPTION_TYPES.map(type => {
              const typeProtocols = protocols.filter(p => p.prescription_type === type);
              if (typeProtocols.length === 0) return null;
              return (
                <View key={type} style={styles.categorySection}>
                  <Text style={styles.categoryTitle}>{type}</Text>
                  {typeProtocols.map(protocol => (
                    <View key={protocol.id} style={styles.itemCard}>
                      <View style={styles.itemInfo}>
                        <Text style={styles.itemName}>{protocol.name}</Text>
                        <Text style={styles.itemMeta} numberOfLines={1}>
                          {protocol.description_short}
                          {protocol.is_easy_day && ' • 🌙 Easy Day'}
                        </Text>
                      </View>
                      <View style={styles.itemActions}>
                        <TouchableOpacity onPress={() => openProtocolModal(protocol)}>
                          <Ionicons name="pencil" size={20} color="#3B82F6" />
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => deleteProtocol(protocol.id)}>
                          <Ionicons name="trash" size={20} color="#EF4444" />
                        </TouchableOpacity>
                      </View>
                    </View>
                  ))}
                </View>
              );
            })}
          </>
        )}
      </ScrollView>

      {/* Exercise Modal */}
      <Modal visible={showExerciseModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={styles.modalTitle}>
                {editingExercise ? 'Edit Exercise' : 'New Exercise'}
              </Text>

              <Text style={styles.inputLabel}>ID (unique, no spaces)</Text>
              <TextInput
                style={styles.input}
                value={exerciseForm.id}
                onChangeText={v => setExerciseForm({...exerciseForm, id: v.toLowerCase().replace(/\s/g, '_')})}
                placeholder="e.g. kb_goblet_squat"
                placeholderTextColor="#666"
                editable={!editingExercise}
              />

              <Text style={styles.inputLabel}>Name</Text>
              <TextInput
                style={styles.input}
                value={exerciseForm.name}
                onChangeText={v => setExerciseForm({...exerciseForm, name: v})}
                placeholder="e.g. KB Goblet Squat"
                placeholderTextColor="#666"
              />

              <Text style={styles.inputLabel}>Category</Text>
              <View style={styles.chipRow}>
                {CATEGORIES.map(cat => (
                  <TouchableOpacity
                    key={cat}
                    style={[styles.chip, exerciseForm.category === cat && styles.chipActive]}
                    onPress={() => setExerciseForm({...exerciseForm, category: cat})}
                  >
                    <Text style={[styles.chipText, exerciseForm.category === cat && styles.chipTextActive]}>
                      {cat}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.inputLabel}>Equipment</Text>
              <View style={styles.chipRow}>
                {EQUIPMENT_OPTIONS.map(equip => (
                  <TouchableOpacity
                    key={equip}
                    style={[styles.chip, exerciseForm.equipment.includes(equip) && styles.chipActive]}
                    onPress={() => toggleEquipment(equip)}
                  >
                    <Text style={[styles.chipText, exerciseForm.equipment.includes(equip) && styles.chipTextActive]}>
                      {equip}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.inputLabel}>Prescription Type</Text>
              <View style={styles.chipRow}>
                {PRESCRIPTION_TYPES.map(type => (
                  <TouchableOpacity
                    key={type}
                    style={[styles.chip, exerciseForm.prescription_type === type && styles.chipActive]}
                    onPress={() => setExerciseForm({...exerciseForm, prescription_type: type})}
                  >
                    <Text style={[styles.chipText, exerciseForm.prescription_type === type && styles.chipTextActive]}>
                      {type.replace('_', ' ')}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <View style={styles.switchRow}>
                <Text style={styles.switchLabel}>Bilateral</Text>
                <Switch
                  value={exerciseForm.bilateral}
                  onValueChange={v => setExerciseForm({...exerciseForm, bilateral: v})}
                  trackColor={{ false: '#333', true: '#4ADE8040' }}
                  thumbColor={exerciseForm.bilateral ? '#4ADE80' : '#666'}
                />
              </View>

              <View style={styles.switchRow}>
                <Text style={styles.switchLabel}>Is Anchor Exercise</Text>
                <Switch
                  value={exerciseForm.is_anchor}
                  onValueChange={v => setExerciseForm({...exerciseForm, is_anchor: v})}
                  trackColor={{ false: '#333', true: '#4ADE8040' }}
                  thumbColor={exerciseForm.is_anchor ? '#4ADE80' : '#666'}
                />
              </View>

              <View style={styles.switchRow}>
                <Text style={styles.switchLabel}>Is Power Exercise</Text>
                <Switch
                  value={exerciseForm.is_power}
                  onValueChange={v => setExerciseForm({...exerciseForm, is_power: v})}
                  trackColor={{ false: '#333', true: '#F59E0B40' }}
                  thumbColor={exerciseForm.is_power ? '#F59E0B' : '#666'}
                />
              </View>

              <View style={styles.modalButtons}>
                <TouchableOpacity style={styles.cancelButton} onPress={() => setShowExerciseModal(false)}>
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.saveButton} onPress={saveExercise}>
                  <Text style={styles.saveButtonText}>Save</Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Protocol Modal */}
      <Modal visible={showProtocolModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={styles.modalTitle}>
                {editingProtocol ? 'Edit Protocol' : 'New Protocol'}
              </Text>

              <Text style={styles.inputLabel}>ID (unique, no spaces)</Text>
              <TextInput
                style={styles.input}
                value={protocolForm.id}
                onChangeText={v => setProtocolForm({...protocolForm, id: v.toLowerCase().replace(/\s/g, '_')})}
                placeholder="e.g. ladder_123"
                placeholderTextColor="#666"
                editable={!editingProtocol}
              />

              <Text style={styles.inputLabel}>Name</Text>
              <TextInput
                style={styles.input}
                value={protocolForm.name}
                onChangeText={v => setProtocolForm({...protocolForm, name: v})}
                placeholder="e.g. Ladder 1-2-3"
                placeholderTextColor="#666"
              />

              <Text style={styles.inputLabel}>Prescription Type</Text>
              <View style={styles.chipRow}>
                {PRESCRIPTION_TYPES.map(type => (
                  <TouchableOpacity
                    key={type}
                    style={[styles.chip, protocolForm.prescription_type === type && styles.chipActive]}
                    onPress={() => setProtocolForm({...protocolForm, prescription_type: type})}
                  >
                    <Text style={[styles.chipText, protocolForm.prescription_type === type && styles.chipTextActive]}>
                      {type.replace('_', ' ')}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.inputLabel}>Description</Text>
              <TextInput
                style={[styles.input, { height: 80 }]}
                value={protocolForm.description_short}
                onChangeText={v => setProtocolForm({...protocolForm, description_short: v})}
                placeholder="Brief description of how to perform..."
                placeholderTextColor="#666"
                multiline
              />

              <Text style={styles.inputLabel}>Example</Text>
              <TextInput
                style={styles.input}
                value={protocolForm.example}
                onChangeText={v => setProtocolForm({...protocolForm, example: v})}
                placeholder="e.g. 5 sets of 5 reps"
                placeholderTextColor="#666"
              />

              <View style={styles.row}>
                <View style={styles.halfInput}>
                  <Text style={styles.inputLabel}>Sets</Text>
                  <TextInput
                    style={styles.input}
                    value={protocolForm.sets}
                    onChangeText={v => setProtocolForm({...protocolForm, sets: v})}
                    placeholder="3-5"
                    placeholderTextColor="#666"
                  />
                </View>
                <View style={styles.halfInput}>
                  <Text style={styles.inputLabel}>Rest</Text>
                  <TextInput
                    style={styles.input}
                    value={protocolForm.rest}
                    onChangeText={v => setProtocolForm({...protocolForm, rest: v})}
                    placeholder="60s"
                    placeholderTextColor="#666"
                  />
                </View>
              </View>

              <View style={styles.row}>
                <View style={styles.halfInput}>
                  <Text style={styles.inputLabel}>Reps</Text>
                  <TextInput
                    style={styles.input}
                    value={protocolForm.reps}
                    onChangeText={v => setProtocolForm({...protocolForm, reps: v})}
                    placeholder="5-8"
                    placeholderTextColor="#666"
                  />
                </View>
                <View style={styles.halfInput}>
                  <Text style={styles.inputLabel}>Tempo</Text>
                  <TextInput
                    style={styles.input}
                    value={protocolForm.tempo}
                    onChangeText={v => setProtocolForm({...protocolForm, tempo: v})}
                    placeholder="3-1-1"
                    placeholderTextColor="#666"
                  />
                </View>
              </View>

              <View style={styles.row}>
                <View style={styles.halfInput}>
                  <Text style={styles.inputLabel}>Hold Time</Text>
                  <TextInput
                    style={styles.input}
                    value={protocolForm.hold_time}
                    onChangeText={v => setProtocolForm({...protocolForm, hold_time: v})}
                    placeholder="10-20s"
                    placeholderTextColor="#666"
                  />
                </View>
                <View style={styles.halfInput}>
                  <Text style={styles.inputLabel}>Time</Text>
                  <TextInput
                    style={styles.input}
                    value={protocolForm.time}
                    onChangeText={v => setProtocolForm({...protocolForm, time: v})}
                    placeholder="30-60s"
                    placeholderTextColor="#666"
                  />
                </View>
              </View>

              <View style={styles.switchRow}>
                <Text style={styles.switchLabel}>Easy Day Protocol</Text>
                <Switch
                  value={protocolForm.is_easy_day}
                  onValueChange={v => setProtocolForm({...protocolForm, is_easy_day: v})}
                  trackColor={{ false: '#333', true: '#4ADE8040' }}
                  thumbColor={protocolForm.is_easy_day ? '#4ADE80' : '#666'}
                />
              </View>

              <View style={styles.modalButtons}>
                <TouchableOpacity style={styles.cancelButton} onPress={() => setShowProtocolModal(false)}>
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.saveButton} onPress={saveProtocol}>
                  <Text style={styles.saveButtonText}>Save</Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  loginContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  backButton: {
    position: 'absolute',
    top: 20,
    left: 20,
  },
  loginTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  loginSubtitle: {
    fontSize: 14,
    color: '#888',
    marginBottom: 32,
    textAlign: 'center',
  },
  passwordInput: {
    width: '100%',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    color: '#fff',
    fontSize: 16,
    marginBottom: 16,
  },
  loginButton: {
    width: '100%',
    backgroundColor: '#4ADE80',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  loginButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: 'bold',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 12,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
  },
  tabActive: {
    backgroundColor: '#4ADE8020',
    borderWidth: 1,
    borderColor: '#4ADE80',
  },
  tabText: {
    color: '#888',
    fontWeight: '600',
  },
  tabTextActive: {
    color: '#4ADE80',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#4ADE8040',
    borderStyle: 'dashed',
  },
  addButtonText: {
    color: '#4ADE80',
    fontSize: 16,
    fontWeight: '600',
  },
  categorySection: {
    marginBottom: 24,
  },
  categoryTitle: {
    color: '#888',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
    letterSpacing: 1,
  },
  itemCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
  },
  itemInfo: {
    flex: 1,
    marginRight: 12,
  },
  itemName: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 4,
  },
  itemMeta: {
    color: '#666',
    fontSize: 12,
  },
  itemActions: {
    flexDirection: 'row',
    gap: 16,
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.9)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    maxHeight: '90%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 20,
    textAlign: 'center',
  },
  inputLabel: {
    color: '#888',
    fontSize: 12,
    marginBottom: 6,
    marginTop: 12,
  },
  input: {
    backgroundColor: '#2a2a2a',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    fontSize: 15,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
  },
  chipActive: {
    backgroundColor: '#4ADE8030',
    borderWidth: 1,
    borderColor: '#4ADE80',
  },
  chipText: {
    color: '#888',
    fontSize: 12,
  },
  chipTextActive: {
    color: '#4ADE80',
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
    paddingVertical: 8,
  },
  switchLabel: {
    color: '#ccc',
    fontSize: 14,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  halfInput: {
    flex: 1,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
    marginBottom: 20,
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#333',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  saveButton: {
    flex: 1,
    backgroundColor: '#4ADE80',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
