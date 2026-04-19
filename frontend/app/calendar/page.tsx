'use client';
import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import DataTable, { TableColumn } from 'react-data-table-component';
import Sidebar from '@/components/Sidebar';
import { contacts as contactsApi, googleCalendar, opportunities as opportunitiesApi } from '@/lib/api';
import { dataTablePaginationOptions, dataTableStyles } from '@/lib/tableStyles';
import { Calendar, Edit, Plus, Search, Trash2, Users } from 'lucide-react';

type EventRow = {
  id: string;
  title: string;
  description?: string | null;
  start_time?: string | null;
  end_time?: string | null;
};

type ContactOption = {
  id: number;
  name: string;
};

type OpportunityOption = {
  id: number;
  title: string;
};

const emptyForm = {
  title: '',
  description: '',
  start_time: '',
  end_time: '',
  attendees: '',
  contact_id: '',
  opportunity_id: '',
};

const formatDateTime = (value?: string | null) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

const toInputDateTime = (value?: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toISOString().slice(0, 16);
};

export default function CalendarPage() {
  const router = useRouter();
  const [eventsList, setEventsList] = useState<EventRow[]>([]);
  const [contactsList, setContactsList] = useState<ContactOption[]>([]);
  const [opportunitiesList, setOpportunitiesList] = useState<OpportunityOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [activeEventId, setActiveEventId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [formData, setFormData] = useState(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [calendarOAuth, setCalendarOAuth] = useState({
    configured: false,
    authorized: false,
  });
  const [calendarTestEmail, setCalendarTestEmail] = useState('');
  const [calendarTestStatus, setCalendarTestStatus] = useState<null | string>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const [events, contacts, opportunities, status] = await Promise.all([
        googleCalendar.listEvents(),
        contactsApi.list(),
        opportunitiesApi.list(),
        googleCalendar.status(),
      ]);
      setEventsList(events.data || []);
      setContactsList(contacts.data || []);
      setOpportunitiesList(opportunities.data || []);
      setCalendarOAuth({
        configured: Boolean(status.data?.oauth_configured),
        authorized: Boolean(status.data?.authorized),
      });
      setCalendarTestEmail(status.data?.test_email || '');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredEvents = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    if (!normalized) return eventsList;
    return eventsList.filter((event) => {
      const titleMatch = event.title?.toLowerCase().includes(normalized);
      const descMatch = (event.description || '').toLowerCase().includes(normalized);
      return titleMatch || descMatch;
    });
  }, [eventsList, search]);

  const openCreateModal = () => {
    const start = new Date(Date.now() + 60 * 60 * 1000);
    const end = new Date(start.getTime() + 30 * 60 * 1000);
    setModalMode('create');
    setActiveEventId(null);
    setFormError(null);
    setFormData({
      title: '',
      description: '',
      start_time: start.toISOString().slice(0, 16),
      end_time: end.toISOString().slice(0, 16),
      attendees: '',
      contact_id: '',
      opportunity_id: '',
    });
    setShowModal(true);
  };

  const openEditModal = (event: EventRow) => {
    setModalMode('edit');
    setActiveEventId(event.id);
    setFormError(null);
    setFormData({
      title: event.title || '',
      description: event.description || '',
      start_time: toInputDateTime(event.start_time),
      end_time: toInputDateTime(event.end_time),
      attendees: '',
      contact_id: '',
      opportunity_id: '',
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!calendarOAuth.authorized) {
      setFormError('Authorize Google Calendar before sending events.');
      return;
    }

    const start = formData.start_time ? new Date(formData.start_time) : null;
    const end = formData.end_time ? new Date(formData.end_time) : null;
    if (start && end && end <= start) {
      setFormError('End time must be after the start time.');
      return;
    }

    const attendees = formData.attendees
      .split(',')
      .map((email) => email.trim())
      .filter(Boolean);

    const payload = {
      title: formData.title,
      description: formData.description || null,
      start_time: start ? start.toISOString() : null,
      end_time: end ? end.toISOString() : null,
      attendees: attendees.length ? attendees : undefined,
      contact_id: formData.contact_id ? parseInt(formData.contact_id) : null,
      opportunity_id: formData.opportunity_id ? parseInt(formData.opportunity_id) : null,
    };

    try {
      if (modalMode === 'create') {
        await googleCalendar.createEvent(payload);
      } else if (activeEventId) {
        await googleCalendar.updateEvent(activeEventId, payload);
      }
      setShowModal(false);
      setActiveEventId(null);
      setFormData(emptyForm);
      loadData();
    } catch (err) {
      console.error(err);
      setFormError('Failed to save event. Check the OAuth status and try again.');
    }
  };

  const handleDelete = async (eventId: string) => {
    if (!confirm('Delete this event?')) return;
    try {
      await googleCalendar.deleteEvent(eventId);
      loadData();
    } catch (err) {
      console.error(err);
      window.alert('Failed to delete event.');
    }
  };

  const handleAuthorizeCalendar = async () => {
    try {
      const redirectUri = `${window.location.origin}/api/auth/callback/calendar`;
      const response = await googleCalendar.oauthAuthorize(redirectUri);
      const authUrl = response.data?.authorization_url;
      if (!authUrl) {
        window.alert('Authorization URL not received.');
        return;
      }
      window.location.assign(authUrl);
    } catch (error) {
      console.error('Failed to start OAuth', error);
      window.alert('Failed to start OAuth. Check console for details.');
    }
  };

  const handleTestCalendar = async () => {
    if (!calendarOAuth.authorized) {
      window.alert('Google Calendar is not authorized yet.');
      return;
    }
    try {
      setCalendarTestStatus('Sending test invite...');
      const start = new Date(Date.now() + 10 * 60 * 1000);
      const end = new Date(start.getTime() + 30 * 60 * 1000);
      await googleCalendar.createEvent({
        title: 'OAuth Test Event',
        description: 'Test event from UM CRM',
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        attendees: calendarTestEmail ? [calendarTestEmail] : undefined,
      });
      setCalendarTestStatus('Test event created. Check your calendar/inbox.');
    } catch (error) {
      console.error('Test event failed', error);
      setCalendarTestStatus('Test event failed. Check console for details.');
    }
  };

  const columns = useMemo<TableColumn<EventRow>[]>(
    () => [
      {
        name: 'Event',
        selector: (row) => row.title,
        sortable: true,
        cell: (row) => (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-blue-50 rounded-full flex items-center justify-center">
              <Calendar size={16} className="text-blue-700" />
            </div>
            <div>
              <div className="font-semibold text-ink">{row.title}</div>
              {row.description ? (
                <div className="text-xs text-muted line-clamp-1">{row.description}</div>
              ) : null}
            </div>
          </div>
        ),
      },
      {
        name: 'Start',
        selector: (row) => row.start_time || '',
        sortable: true,
        cell: (row) => <span className="text-muted">{formatDateTime(row.start_time)}</span>,
        width: '220px',
      },
      {
        name: 'End',
        selector: (row) => row.end_time || '',
        sortable: true,
        cell: (row) => <span className="text-muted">{formatDateTime(row.end_time)}</span>,
        width: '220px',
      },
      {
        name: 'Actions',
        cell: (row) => (
          <div className="flex justify-end gap-3">
            <button
              onClick={() => openEditModal(row)}
              className="text-muted hover:text-blue-700"
              aria-label="Edit event"
            >
              <Edit size={18} />
            </button>
            <button
              onClick={() => handleDelete(row.id)}
              className="text-muted hover:text-rose-600"
              aria-label="Delete event"
            >
              <Trash2 size={18} />
            </button>
          </div>
        ),
        width: '130px',
      },
    ],
    []
  );

  if (loading) {
    return (
      <div className="flex">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-muted">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col md:flex-row min-h-screen">
      <Sidebar />
      <div className="flex-1 p-6 lg:p-10">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-6">
          <div>
            <div className="page-kicker">Meeting Center</div>
            <h1 className="page-title mt-2">Calendar</h1>
            <p className="text-muted mt-2">Plan meetings with attendees linked to your pipeline.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button onClick={openCreateModal} className="btn-primary flex items-center gap-2">
              <Plus size={18} />
              Add Event
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[2fr,3fr] gap-6 mb-6">
          <div className="card card-elevated">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-muted">Google Calendar</div>
                <h2 className="text-xl font-semibold text-ink mt-2">Connection</h2>
                <p className="text-sm text-muted mt-2">
                  OAuth configured: {calendarOAuth.configured ? 'yes' : 'no'} · Authorized: {calendarOAuth.authorized ? 'yes' : 'no'}
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl flex items-center justify-center shadow-soft">
                <Calendar size={20} className="text-white" />
              </div>
            </div>
            <div className="flex flex-wrap gap-3 mt-4">
              <button
                className="btn-primary"
                onClick={handleAuthorizeCalendar}
                disabled={!calendarOAuth.configured}
              >
                Authorize
              </button>
              <button
                className="btn-ghost"
                onClick={handleTestCalendar}
                disabled={!calendarOAuth.authorized}
              >
                Send Test Invite
              </button>
              <Link href="/settings" className="btn-ghost">
                Upload OAuth JSON
              </Link>
            </div>
            {calendarTestStatus ? (
              <div className="text-sm text-ink mt-3">{calendarTestStatus}</div>
            ) : null}
            {!calendarOAuth.configured ? (
              <div className="text-xs text-muted mt-2">
                Upload credentials in Settings before authorizing.
              </div>
            ) : null}
          </div>

          <div className="card card-elevated">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-muted">Search</div>
                <h2 className="text-xl font-semibold text-ink mt-2">Event Workspace</h2>
                <p className="text-sm text-muted mt-2">Filter events and keep the timeline clean.</p>
              </div>
              <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center">
                <Users size={20} className="text-blue-700" />
              </div>
            </div>
            <div className="relative mt-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={18} />
              <input
                type="text"
                placeholder="Search events..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="input-field pl-10"
              />
            </div>
          </div>
        </div>

        <div className="card overflow-hidden">
          <DataTable
            columns={columns}
            data={filteredEvents}
            pagination
            paginationComponentOptions={dataTablePaginationOptions}
            customStyles={dataTableStyles}
            highlightOnHover
          />
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="modal-panel w-full max-w-2xl p-6 relative animate-fade-up">
            <button
              className="absolute top-3 right-3 text-muted"
              onClick={() => setShowModal(false)}
            >
              &times;
            </button>
            <h3 className="text-lg font-semibold text-ink mb-2">
              {modalMode === 'create' ? 'Create event' : 'Edit event'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-ink mb-1">Title</label>
                  <input
                    className="input-field"
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-ink mb-1">Description</label>
                  <textarea
                    className="input-field min-h-[100px]"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Start</label>
                  <input
                    className="input-field"
                    type="datetime-local"
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">End</label>
                  <input
                    className="input-field"
                    type="datetime-local"
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    required
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-ink mb-1">Attendees</label>
                  <input
                    className="input-field"
                    type="text"
                    placeholder="alex@acme.com, jamie@acme.com"
                    value={formData.attendees}
                    onChange={(e) => setFormData({ ...formData, attendees: e.target.value })}
                  />
                  <p className="text-xs text-muted mt-1">Separate multiple emails with commas.</p>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Link to Contact</label>
                  <select
                    className="input-field"
                    value={formData.contact_id}
                    onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
                  >
                    <option value="">No contact</option>
                    {contactsList.map((contact) => (
                      <option key={contact.id} value={contact.id}>
                        {contact.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Link to Opportunity</label>
                  <select
                    className="input-field"
                    value={formData.opportunity_id}
                    onChange={(e) => setFormData({ ...formData, opportunity_id: e.target.value })}
                  >
                    <option value="">No opportunity</option>
                    {opportunitiesList.map((opp) => (
                      <option key={opp.id} value={opp.id}>
                        {opp.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {formError ? <div className="text-sm text-rose-600">{formError}</div> : null}

              <div className="flex justify-end gap-2">
                <button type="button" className="btn-ghost" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {modalMode === 'create' ? 'Create event' : 'Save changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
