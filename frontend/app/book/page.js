import React from 'react'
import dynamic from 'next/dynamic';

const Flipbook = dynamic(() => import('@/components/Flipbook'), {
  ssr: false,
});

export default function page() {
  return (
    <div>
      <Flipbook/>
    </div>
  )
}
