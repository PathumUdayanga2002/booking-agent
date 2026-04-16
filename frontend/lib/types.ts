export type UserRole = "user" | "admin";

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
};

export type Room = {
  _id: string;
  name: string;
  description: string;
  pricePerNight: number;
  capacity: number;
  totalUnits: number;
  facilities: string[];
  availableUnits: number;
};

export type Booking = {
  _id: string;
  userId?: string;
  roomId?: string | (Omit<Room, "availableUnits"> & { pricePerNight: number });
  roomNameSnapshot: string;
  checkIn: string;
  checkOut: string;
  nights: number;
  guests: number;
  guestName: string;
  guestEmail: string;
  guestPhone: string;
  totalAmount: number;
  status: "confirmed" | "cancelled";
  createdAt?: string;
  updatedAt?: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "agent";
  content: string;
  timestamp: string;
  toolUsage?: {
    toolName: string;
    input: unknown;
    output: unknown;
  };
  status?: "sending" | "sent" | "error";
};

export type Document = {
  id: string;
  filename: string;
  sourceType: "pdf" | "txt";
  uploadedAt: string;
  chunks: number;
  status: "processing" | "stored" | "error";
  errorMessage?: string;
};
