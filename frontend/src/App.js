import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Textarea } from './components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Phone, Plus, Edit, Trash2, Smartphone, Copy, Download, AlertCircle, CheckCircle } from 'lucide-react';
import { Alert, AlertDescription } from './components/ui/alert';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    phone_number: '',
    text: ''
  });
  const [editingContact, setEditingContact] = useState(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showNdefDialog, setShowNdefDialog] = useState(false);
  const [selectedContact, setSelectedContact] = useState(null);
  const [alert, setAlert] = useState(null);

  // Fetch contacts from API
  const fetchContacts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/contacts`);
      if (response.ok) {
        const data = await response.json();
        setContacts(data);
      } else {
        showAlert('Fehler beim Laden der Kontakte', 'error');
      }
    } catch (error) {
      showAlert('Verbindungsfehler beim Laden der Kontakte', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Show alert message
  const showAlert = (message, type = 'info') => {
    setAlert({ message, type });
    setTimeout(() => setAlert(null), 5000);
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.phone_number || !formData.text) {
      showAlert('Telefonnummer und Text sind erforderlich', 'error');
      return;
    }

    try {
      const url = editingContact 
        ? `${API_BASE_URL}/api/contacts/${editingContact.id}`
        : `${API_BASE_URL}/api/contacts`;
      
      const method = editingContact ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        showAlert(
          editingContact ? 'Kontakt erfolgreich aktualisiert' : 'Kontakt erfolgreich erstellt', 
          'success'
        );
        fetchContacts();
        resetForm();
        setShowAddDialog(false);
        setShowEditDialog(false);
      } else {
        const error = await response.json();
        showAlert(error.detail || 'Fehler beim Speichern', 'error');
      }
    } catch (error) {
      showAlert('Verbindungsfehler beim Speichern', 'error');
    }
  };

  // Handle contact deletion
  const handleDelete = async (contactId) => {
    if (!window.confirm('Möchten Sie diesen Kontakt wirklich löschen?')) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/contacts/${contactId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        showAlert('Kontakt erfolgreich gelöscht', 'success');
        fetchContacts();
      } else {
        showAlert('Fehler beim Löschen', 'error');
      }
    } catch (error) {
      showAlert('Verbindungsfehler beim Löschen', 'error');
    }
  };

  // Reset form
  const resetForm = () => {
    setFormData({ name: '', phone_number: '', text: '' });
    setEditingContact(null);
  };

  // Handle edit
  const handleEdit = (contact) => {
    setFormData({
      name: contact.name,
      phone_number: contact.phone_number,
      text: contact.text
    });
    setEditingContact(contact);
    setShowEditDialog(true);
  };

  // Handle NDEF view
  const handleViewNdef = (contact) => {
    setSelectedContact(contact);
    setShowNdefDialog(true);
  };

  // Copy to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    showAlert('In Zwischenablage kopiert', 'success');
  };

  // Download NDEF data
  const downloadNdefData = (contact) => {
    const data = atob(contact.ndef_data);
    const blob = new Blob([data], { type: 'text/vcard' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${contact.name || contact.phone_number}_nfc.vcf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    fetchContacts();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Smartphone className="w-8 h-8 text-slate-700 mr-3" />
            <h1 className="text-3xl font-bold text-slate-800">NFC Kontakt Manager</h1>
          </div>
          <p className="text-slate-600 text-lg">
            Verwalten Sie Kontakte für NFC 215 Tags
          </p>
        </div>

        {/* Alert */}
        {alert && (
          <Alert className={`mb-6 ${alert.type === 'error' ? 'border-red-500 bg-red-50' : 
            alert.type === 'success' ? 'border-green-500 bg-green-50' : 'border-blue-500 bg-blue-50'}`}>
            {alert.type === 'error' ? <AlertCircle className="h-4 w-4" /> : <CheckCircle className="h-4 w-4" />}
            <AlertDescription className={alert.type === 'error' ? 'text-red-800' : 
              alert.type === 'success' ? 'text-green-800' : 'text-blue-800'}>
              {alert.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Add Contact Button */}
        <div className="flex justify-center mb-6">
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button className="bg-slate-800 hover:bg-slate-700 text-white px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200">
                <Plus className="w-5 h-5 mr-2" />
                Neuen Kontakt hinzufügen
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Neuen Kontakt hinzufügen</DialogTitle>
                <DialogDescription>
                  Erstellen Sie einen neuen Kontakt für NFC 215 Tags
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="name">Name (optional)</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="z.B. Max Mustermann"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="phone_number">Telefonnummer *</Label>
                  <Input
                    id="phone_number"
                    value={formData.phone_number}
                    onChange={(e) => setFormData({...formData, phone_number: e.target.value})}
                    placeholder="z.B. +49 123 456789"
                    required
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="text">Zusätzlicher Text *</Label>
                  <Textarea
                    id="text"
                    value={formData.text}
                    onChange={(e) => setFormData({...formData, text: e.target.value})}
                    placeholder="z.B. Geschäftlich, Notfall, etc."
                    required
                    rows={3}
                    className="mt-1"
                  />
                  <p className="text-sm text-slate-500 mt-1">
                    Maximale Größe für NFC 215: 504 Bytes
                  </p>
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => {
                      setShowAddDialog(false);
                      resetForm();
                    }}
                  >
                    Abbrechen
                  </Button>
                  <Button type="submit" className="bg-slate-800 hover:bg-slate-700">
                    Erstellen
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Contacts Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-800 mx-auto"></div>
            <p className="text-slate-600 mt-4">Kontakte werden geladen...</p>
          </div>
        ) : contacts.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <Phone className="w-16 h-16 text-slate-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-700 mb-2">
                Keine Kontakte vorhanden
              </h3>
              <p className="text-slate-500">
                Fügen Sie Ihren ersten Kontakt hinzu, um zu beginnen.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {contacts.map((contact) => (
              <Card key={contact.id} className="hover:shadow-lg transition-shadow duration-200">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center justify-between">
                    <span className="text-lg">
                      {contact.name || contact.phone_number}
                    </span>
                    <Badge variant={contact.data_size <= 504 ? "default" : "destructive"}>
                      {contact.data_size}B
                    </Badge>
                  </CardTitle>
                  <CardDescription>
                    <div className="flex items-center">
                      <Phone className="w-4 h-4 mr-2" />
                      {contact.phone_number}
                    </div>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-600 mb-4 line-clamp-2">
                    {contact.text}
                  </p>
                  <Separator className="mb-4" />
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEdit(contact)}
                      className="flex-1"
                    >
                      <Edit className="w-4 h-4 mr-1" />
                      Bearbeiten
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleViewNdef(contact)}
                      className="flex-1"
                    >
                      <Smartphone className="w-4 h-4 mr-1" />
                      NFC
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete(contact.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Edit Dialog */}
        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Kontakt bearbeiten</DialogTitle>
              <DialogDescription>
                Ändern Sie die Kontaktdaten
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="edit_name">Name (optional)</Label>
                <Input
                  id="edit_name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="z.B. Max Mustermann"
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="edit_phone_number">Telefonnummer *</Label>
                <Input
                  id="edit_phone_number"
                  value={formData.phone_number}
                  onChange={(e) => setFormData({...formData, phone_number: e.target.value})}
                  placeholder="z.B. +49 123 456789"
                  required
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="edit_text">Zusätzlicher Text *</Label>
                <Textarea
                  id="edit_text"
                  value={formData.text}
                  onChange={(e) => setFormData({...formData, text: e.target.value})}
                  placeholder="z.B. Geschäftlich, Notfall, etc."
                  required
                  rows={3}
                  className="mt-1"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => {
                    setShowEditDialog(false);
                    resetForm();
                  }}
                >
                  Abbrechen
                </Button>
                <Button type="submit" className="bg-slate-800 hover:bg-slate-700">
                  Aktualisieren
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* NDEF Dialog */}
        <Dialog open={showNdefDialog} onOpenChange={setShowNdefDialog}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>NFC Daten für {selectedContact?.name || selectedContact?.phone_number}</DialogTitle>
              <DialogDescription>
                Bereit für NFC 215 Tag ({selectedContact?.data_size} Bytes von 504 Bytes verwendet)
              </DialogDescription>
            </DialogHeader>
            {selectedContact && (
              <div className="space-y-4">
                <div className="bg-slate-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">Kontakt Informationen:</h4>
                  <p><strong>Name:</strong> {selectedContact.name || 'Nicht angegeben'}</p>
                  <p><strong>Telefon:</strong> {selectedContact.phone_number}</p>
                  <p><strong>Text:</strong> {selectedContact.text}</p>
                </div>
                
                <div className="bg-slate-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">vCard Daten (Base64):</h4>
                  <div className="bg-white p-3 rounded border font-mono text-sm break-all">
                    {selectedContact.ndef_data}
                  </div>
                  <div className="flex space-x-2 mt-3">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => copyToClipboard(selectedContact.ndef_data)}
                      className="flex-1"
                    >
                      <Copy className="w-4 h-4 mr-1" />
                      Kopieren
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => downloadNdefData(selectedContact)}
                      className="flex-1"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      Download
                    </Button>
                  </div>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2 text-blue-800">Anleitung:</h4>
                  <ol className="text-sm text-blue-700 space-y-1">
                    <li>1. Installieren Sie eine NFC-App (z.B. "NFC Tools" oder "TagWriter")</li>
                    <li>2. Wählen Sie "vCard" oder "Kontakt" als Datentyp</li>
                    <li>3. Fügen Sie die kopierten Daten ein oder nutzen Sie die Download-Datei</li>
                    <li>4. Halten Sie Ihr Gerät an den NFC 215 Tag zum Schreiben</li>
                  </ol>
                </div>

                <div className="flex justify-end">
                  <Button onClick={() => setShowNdefDialog(false)}>
                    Schließen
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default App;