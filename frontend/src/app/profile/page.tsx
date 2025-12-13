import React from 'react';
import Navbar from '@/components/ui/Navbar';
import UserProfile from '@/components/profile/UserProfile';

export default function ProfilePage() {
    return (
        <main className="min-h-screen bg-slate-50">
            {/* Shared Navbar */}
            <Navbar />
            
            {/* Profile Content Component */}
            <div className="pt-24 md:pt-28">
                 <UserProfile />
            </div>
        </main>
    );
}
