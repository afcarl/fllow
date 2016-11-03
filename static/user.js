const datify = (time, i) => ({x: new Date(time*1000), y: i+1});

var chart = new Chartist.Line('.ct-chart', {
  series: [
    {
      name: 'series-1',
      data: FOLLOWED.map(datify)
    },
    {
      name: 'series-2',
      data: UNFOLLOWED.map(datify)
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
