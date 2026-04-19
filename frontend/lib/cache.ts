const CACHE_PREFIX = 'um_crm_cache_';
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

interface CacheItem<T> {
  data: T;
  timestamp: number;
}

function getCacheKey(key: string): string {
  return `${CACHE_PREFIX}${key}`;
}

export function setCache<T>(key: string, data: T): void {
  try {
    const item: CacheItem<T> = {
      data,
      timestamp: Date.now(),
    };
    localStorage.setItem(getCacheKey(key), JSON.stringify(item));
  } catch (error) {
    console.error(`[Cache] Error setting ${key}:`, error);
  }
}

export function getCache<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(getCacheKey(key));
    if (!raw) return null;

    const item: CacheItem<T> = JSON.parse(raw);
    
    if (Date.now() - item.timestamp > CACHE_TTL) {
      localStorage.removeItem(getCacheKey(key));
      return null;
    }

    return item.data;
  } catch (error) {
    console.error(`[Cache] Error getting ${key}:`, error);
    return null;
  }
}

export function isCacheValid(key: string): boolean {
  try {
    const raw = localStorage.getItem(getCacheKey(key));
    if (!raw) return false;

    const item = JSON.parse(raw);
    return Date.now() - item.timestamp <= CACHE_TTL;
  } catch {
    return false;
  }
}

export function clearCache(key?: string): void {
  if (key) {
    localStorage.removeItem(getCacheKey(key));
  } else {
    Object.keys(localStorage)
      .filter(k => k.startsWith(CACHE_PREFIX))
      .forEach(k => localStorage.removeItem(k));
  }
}

export async function preloadUserData() {
  const { api } = await import('./api');
  
  try {
    const [contacts, opportunities, tasks, activities, metrics, pipeline] = await Promise.all([
      api.get('/api/contacts'),
      api.get('/api/opportunities'),
      api.get('/api/tasks'),
      api.get('/api/activities'),
      api.get('/api/reports/dashboard'),
      api.get('/api/reports/pipeline'),
    ]);

    setCache('contacts', contacts.data);
    setCache('opportunities', opportunities.data);
    setCache('tasks', tasks.data);
    setCache('activities', activities.data);
    setCache('metrics', metrics.data);
    setCache('pipeline', pipeline.data);

    console.log('[Cache] All user data preloaded successfully');
    return true;
  } catch (error) {
    console.error('[Cache] Preload failed:', error);
    return false;
  }
}

export function getPreloadedData() {
  return {
    contacts: getCache<any[]>('contacts'),
    opportunities: getCache<any[]>('opportunities'),
    tasks: getCache<any[]>('tasks'),
    activities: getCache<any[]>('activities'),
    metrics: getCache<any>('metrics'),
    pipeline: getCache<any[]>('pipeline'),
  };
}