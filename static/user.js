function datify(times) {
    const data = times.map((t, i) => ({x: new Date(t*1000), y: i+1}));
    // add a dummy value with current time, for better chart range:
    if (data.length) data.push({x: new Date(), y: data[data.length-1].y})
    return data;
};

var chart = new Chartist.Line('.ct-chart', {
  series: [
    {
      name: 'series-1',
      data: datify(FOLLOWED)
    },
    {
      name: 'series-2',
      data: datify(UNFOLLOWED)
    }
  ]
}, {
  axisX: {
    type: Chartist.FixedScaleAxis,
    divisor: 5,
    labelInterpolationFnc: function(value) {
      return moment(value).format('MMM D');
    }
  }
});
