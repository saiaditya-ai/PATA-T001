export const geocodeAddress = async (address) => {
  try {
    const response = await fetch('http://localhost:8000/geocode', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ raw_address: address }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Geocoding failed:", error);
    throw error;
  }
};
